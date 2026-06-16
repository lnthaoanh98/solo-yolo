# AI Content Strategist Agent

Agent web chat dùng LangChain, Pandas và Plotly để phân tích hiệu suất nội dung TikTok, YouTube hoặc Facebook từ file CSV/Excel.

## Tính năng

- Upload CSV/Excel chứa dữ liệu video.
- Chấm điểm hiệu suất từng video.
- Xác định content pillar hiệu quả nhất.
- Tìm khung giờ đăng tối ưu.
- Phát hiện pattern thắng/thua.
- Dự báo tăng trưởng 30 ngày.
- Đề xuất content calendar cho tháng tiếp theo.
- Sinh dashboard và executive summary.

## Cấu hình LLM

Tạo file `.env` từ `.env.example`:

```powershell
Copy-Item .env.example .env
```

Điền provider OpenAI-compatible:

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key
LLM_MODEL=gpt-4o-mini
```

Nếu chưa cấu hình LLM, app vẫn chạy ở fallback mode và dùng summary deterministic từ dữ liệu.

## Chạy local

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Mở `http://127.0.0.1:8080`.

## Test nhanh

```powershell
pytest
```

File mẫu nằm tại `sample_data/content_performance_sample.csv`.

## Docker

```powershell
docker build -t ai-content-strategist-agent .
docker run --env-file .env -p 8080:8080 ai-content-strategist-agent
```

## Cột dữ liệu khuyến nghị

App tự map nhiều tên cột phổ biến. Các cột tốt nhất gồm:

| Nhóm | Tên cột gợi ý |
| --- | --- |
| Nội dung | `title`, `platform`, `content_pillar` |
| Thời gian | `posted_at` |
| Hiệu suất | `views`, `likes`, `comments`, `shares`, `saves`, `followers_gained` |
| Retention | `duration_seconds`, `avg_watch_duration` |

