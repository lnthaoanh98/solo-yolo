from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.agent import ContentStrategistAgent
from app.analysis import analyze_video_dataframe, load_video_file


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SAMPLE_DIR = BASE_DIR.parent / "sample_data"

app = FastAPI(title="AI Content Strategist Agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/sample-data", StaticFiles(directory=SAMPLE_DIR), name="sample-data")

agent = ContentStrategistAgent()


@dataclass
class DatasetState:
    filename: str
    rows: int
    analysis: dict[str, Any]


DATASETS: dict[str, DatasetState] = {}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    dataset_id: str | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "llm_configured": agent.ready}


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)) -> JSONResponse:
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File upload đang rỗng.")

    try:
        raw_df = await run_in_threadpool(load_video_file, contents, file.filename or "dataset.csv")
        analysis = await run_in_threadpool(analyze_video_dataframe, raw_df)
        executive_summary = await run_in_threadpool(agent.create_executive_summary, analysis)
        analysis["executive_summary"] = executive_summary
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Không thể phân tích file: {exc}") from exc

    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = DatasetState(filename=file.filename or "dataset", rows=len(raw_df), analysis=analysis)

    return JSONResponse(
        {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": len(raw_df),
            "llm_configured": agent.ready,
            "analysis": analysis,
        }
    )


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    state = DATASETS.get(request.dataset_id or "") if request.dataset_id else None
    answer = await run_in_threadpool(agent.answer, request.message, state.analysis if state else None)
    return {"answer": answer, "dataset_id": request.dataset_id, "llm_configured": agent.ready}


@app.get("/api/report/{dataset_id}")
def report(dataset_id: str) -> dict[str, Any]:
    state = DATASETS.get(dataset_id)
    if not state:
        raise HTTPException(status_code=404, detail="Không tìm thấy dataset.")
    return {"dataset_id": dataset_id, "filename": state.filename, "rows": state.rows, "analysis": state.analysis}


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
