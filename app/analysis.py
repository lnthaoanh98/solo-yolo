from __future__ import annotations

import calendar as calendar_lib
import json
import math
import re
from datetime import date, datetime, time, timedelta
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


FIELD_SYNONYMS: dict[str, list[str]] = {
    "video_id": ["video_id", "id", "post_id", "content_id", "url", "video_url"],
    "title": ["title", "video_title", "caption", "title_caption", "description", "content_title", "post_text"],
    "platform": ["platform", "channel", "source", "network"],
    "posted_at": [
        "posted_at",
        "publish_date",
        "publish_time",
        "upload_date",
        "created_time",
        "created_at",
        "date",
        "post_time",
    ],
    "content_pillar": ["content_pillar", "content pillar", "pillar", "category", "content_category", "topic", "series"],
    "views": ["views", "view_count", "plays", "video_views", "watch_count"],
    "likes": ["likes", "like", "like_count", "likes_count", "reactions", "reaction_count"],
    "comments": ["comments", "comment", "comment_count", "comments_count", "replies"],
    "shares": ["shares", "share", "share_count", "shares_count", "reposts"],
    "saves": ["saves", "save_count", "favorites", "bookmarks"],
    "followers_gained": [
        "followers_gained",
        "new_followers",
        "follows",
        "subscribers_gained",
        "new_subscribers",
        "net_followers",
    ],
    "watch_time": ["watch_time", "total_watch_time", "watch_time_seconds", "watch_time_minutes", "watch_time_hours"],
    "avg_watch_duration": [
        "avg_watch_duration",
        "average_watch_duration",
        "avg_view_duration",
        "average_view_duration",
        "avg_watch_time",
        "avg_watch_time_s",
        "avg_watch_time_sec",
        "avg_watch_time_seconds",
    ],
    "duration_seconds": [
        "duration_seconds",
        "duration",
        "duration_s",
        "duration_sec",
        "video_duration",
        "video_duration_s",
        "video_duration_sec",
        "video_duration_seconds",
        "length",
        "video_length",
    ],
    "reach": ["reach", "people_reached", "unique_viewers"],
    "impressions": ["impressions", "impression_count"],
    "engagement_rate": ["engagement_rate", "er", "engagement_pct", "engagement_percent"],
    "retention_rate": [
        "retention_rate",
        "completion_rate",
        "completion_pct",
        "completion_percent",
        "avg_completion_rate",
        "avg_watch",
        "avg_watch_pct",
        "avg_watch_percent",
        "avg_watch_percentage",
        "average_watch_percent",
        "watch_percent",
        "watch_percentage",
    ],
}

POSTED_DATE_SYNONYMS = [
    "posted_date",
    "post_date",
    "publish_date",
    "upload_date",
    "created_date",
    "date",
]

POSTED_TIME_SYNONYMS = [
    "posted_time",
    "post_time",
    "publish_time",
    "upload_time",
    "created_time",
    "time",
]

NUMERIC_COUNT_FIELDS = [
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "followers_gained",
    "watch_time",
    "reach",
    "impressions",
]

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAY_LABELS = {
    "Monday": "T2",
    "Tuesday": "T3",
    "Wednesday": "T4",
    "Thursday": "T5",
    "Friday": "T6",
    "Saturday": "T7",
    "Sunday": "CN",
}
VI_WEEKDAY_TO_NUM = {"T2": 0, "T3": 1, "T4": 2, "T5": 3, "T6": 4, "T7": 5, "CN": 6}


def load_video_file(contents: bytes, filename: str) -> pd.DataFrame:
    """Load an uploaded CSV or Excel file into a DataFrame."""
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    buffer = BytesIO(contents)

    if suffix == "csv":
        try:
            df = pd.read_csv(buffer)
        except UnicodeDecodeError:
            buffer.seek(0)
            df = pd.read_csv(buffer, encoding="utf-8-sig")
        except Exception:
            buffer.seek(0)
            df = pd.read_csv(buffer, encoding="latin1")
    elif suffix in {"xlsx", "xls"}:
        df = pd.read_excel(buffer)
    else:
        raise ValueError("Vui lòng upload file .csv, .xlsx hoặc .xls.")

    if df.empty:
        raise ValueError("File không có dòng dữ liệu nào để phân tích.")

    return df


def analyze_video_dataframe(raw_df: pd.DataFrame) -> dict[str, Any]:
    prepared, schema = prepare_video_data(raw_df)
    pillar_performance = build_pillar_performance(prepared)
    optimal_time = build_optimal_time(prepared)
    patterns = detect_patterns(prepared, pillar_performance, optimal_time)
    forecast = build_growth_forecast(prepared)
    content_calendar = build_content_calendar(prepared, pillar_performance, optimal_time)
    per_video = build_per_video(prepared)
    charts = build_dashboard_charts(prepared, pillar_performance, optimal_time, forecast)

    summary = build_summary(
        prepared=prepared,
        pillar_performance=pillar_performance,
        optimal_time=optimal_time,
        forecast=forecast,
        content_calendar=content_calendar,
    )

    return _json_ready(
        {
            "summary": summary,
            "schema": schema,
            "per_video": per_video,
            "pillar_performance": pillar_performance,
            "optimal_time": optimal_time,
            "patterns": patterns,
            "growth_forecast": forecast,
            "content_calendar": content_calendar,
            "charts": charts,
        }
    )


def prepare_video_data(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = raw_df.copy()
    raw.columns = [str(column).strip() for column in raw.columns]
    lookup = {_canonicalize(column): column for column in raw.columns}

    data = pd.DataFrame(index=raw.index)
    field_map: dict[str, str] = {}

    for field, synonyms in FIELD_SYNONYMS.items():
        source = _find_column(lookup, synonyms)
        if source:
            field_map[field] = source
            data[field] = raw[source]
        else:
            data[field] = np.nan

    data["video_id"] = data["video_id"].where(_not_blank(data["video_id"]))
    data["video_id"] = data["video_id"].fillna(pd.Series([f"video-{idx + 1:03d}" for idx in range(len(data))]))

    data["title"] = data["title"].fillna("").astype(str).str.strip()
    data.loc[data["title"] == "", "title"] = [f"Video {idx + 1}" for idx in range(len(data))]

    data["platform"] = data["platform"].fillna("Unknown").astype(str).str.strip()
    data.loc[data["platform"] == "", "platform"] = "Unknown"

    data["content_pillar"] = data["content_pillar"].where(_not_blank(data["content_pillar"]))
    data["content_pillar"] = data["content_pillar"].fillna(data["title"].map(infer_content_pillar))
    data["content_pillar"] = data["content_pillar"].astype(str).str.strip().replace("", "Uncategorized")

    data["posted_at_dt"] = _build_posted_datetime(raw, lookup, field_map, data["posted_at"])
    data["posted_date"] = data["posted_at_dt"].dt.date
    data["posted_hour"] = data["posted_at_dt"].dt.hour
    data["posted_weekday"] = data["posted_at_dt"].dt.day_name()
    data["posted_weekday_label"] = data["posted_weekday"].map(WEEKDAY_LABELS)

    for field in NUMERIC_COUNT_FIELDS:
        data[field] = _to_numeric_series(data[field]).fillna(0)

    data["duration_seconds"] = data["duration_seconds"].map(_parse_duration_seconds).fillna(0)
    data["avg_watch_duration"] = data["avg_watch_duration"].map(_parse_duration_seconds).fillna(0)
    data["retention_rate_provided"] = _normalize_rate_percent(data["retention_rate"])
    data["engagement_rate_provided"] = _normalize_rate_percent(data["engagement_rate"])

    data["reach_base"] = data["views"].copy()
    for fallback in ["impressions", "reach"]:
        data["reach_base"] = data["reach_base"].where(data["reach_base"] > 0, data[fallback])
    data["reach_base"] = data["reach_base"].fillna(0)

    data["engagements"] = data[["likes", "comments", "shares", "saves"]].sum(axis=1)
    data["engagement_rate"] = _safe_divide(data["engagements"], data["reach_base"]) * 100
    data["engagement_rate"] = data["engagement_rate_provided"].where(
        data["engagement_rate_provided"].notna() & (data["engagement_rate_provided"] > 0),
        data["engagement_rate"],
    )
    data["followers_per_1k_views"] = _safe_divide(data["followers_gained"], data["reach_base"]) * 1000
    data["shares_per_1k_views"] = _safe_divide(data["shares"], data["reach_base"]) * 1000
    data["saves_per_1k_views"] = _safe_divide(data["saves"], data["reach_base"]) * 1000

    computed_completion = _safe_divide(data["avg_watch_duration"], data["duration_seconds"]) * 100
    data["completion_rate"] = data["retention_rate_provided"].where(
        data["retention_rate_provided"].notna() & (data["retention_rate_provided"] > 0),
        computed_completion,
    )
    data["completion_rate"] = data["completion_rate"].clip(lower=0, upper=100)

    title_text = data["title"].fillna("").astype(str)
    data["title_length"] = title_text.str.len()
    data["hashtag_count"] = title_text.str.count("#")
    data["question_hook"] = title_text.str.contains(r"\?|why|how|cách|vì sao|làm sao", case=False, regex=True)
    data["list_hook"] = title_text.str.contains(r"\b\d+\b|top|tips|bước|lý do", case=False, regex=True)
    data["duration_bucket"] = data["duration_seconds"].map(_duration_bucket)

    data["performance_score"] = compute_performance_score(data)
    data["rank"] = data["performance_score"].rank(method="min", ascending=False).astype(int)
    data["performance_tier"] = data["performance_score"].map(_tier_from_score)

    missing_fields = sorted(set(FIELD_SYNONYMS) - set(field_map))
    return data, {"field_map": field_map, "missing_fields": missing_fields, "row_count": int(len(data))}


def build_per_video(data: pd.DataFrame) -> list[dict[str, Any]]:
    columns = [
        "rank",
        "video_id",
        "title",
        "platform",
        "content_pillar",
        "posted_at_dt",
        "views",
        "likes",
        "comments",
        "shares",
        "saves",
        "followers_gained",
        "engagements",
        "engagement_rate",
        "completion_rate",
        "duration_bucket",
        "performance_score",
        "performance_tier",
    ]
    per_video = data[columns].copy()
    per_video["posted_at"] = per_video["posted_at_dt"].map(_format_datetime)
    per_video = per_video.drop(columns=["posted_at_dt"]).sort_values(["rank", "performance_score"])
    return _records(per_video)


def build_pillar_performance(data: pd.DataFrame) -> list[dict[str, Any]]:
    if data.empty:
        return []

    grouped = (
        data.groupby("content_pillar", dropna=False)
        .agg(
            videos=("video_id", "count"),
            total_views=("views", "sum"),
            median_views=("views", "median"),
            total_engagements=("engagements", "sum"),
            avg_engagement_rate=("engagement_rate", "mean"),
            total_followers_gained=("followers_gained", "sum"),
            avg_completion_rate=("completion_rate", "mean"),
            avg_score=("performance_score", "mean"),
            median_score=("performance_score", "median"),
        )
        .reset_index()
    )

    winners = data.sort_values("performance_score", ascending=False).drop_duplicates("content_pillar")
    top_lookup = winners.set_index("content_pillar")["title"].to_dict()
    grouped["top_video"] = grouped["content_pillar"].map(top_lookup)
    grouped["score_per_video"] = grouped["avg_score"]
    grouped = grouped.sort_values(["score_per_video", "videos"], ascending=[False, False])
    return _records(grouped)


def build_optimal_time(data: pd.DataFrame) -> dict[str, Any]:
    timed = data[data["posted_at_dt"].notna()].copy()
    if timed.empty:
        return {
            "available": False,
            "top_slots": [],
            "heatmap": [],
            "note": "File chưa có cột ngày/giờ đăng hợp lệ.",
        }

    grouped = (
        timed.groupby(["posted_weekday", "posted_weekday_label", "posted_hour"], dropna=False)
        .agg(
            videos=("video_id", "count"),
            avg_score=("performance_score", "mean"),
            median_views=("views", "median"),
            avg_engagement_rate=("engagement_rate", "mean"),
        )
        .reset_index()
    )
    grouped["slot"] = grouped["posted_weekday_label"].fillna("?") + " " + grouped["posted_hour"].fillna(0).astype(int).astype(str).str.zfill(2) + ":00"
    grouped = grouped.sort_values(["avg_score", "median_views"], ascending=[False, False])

    pivot = (
        timed.pivot_table(
            index="posted_weekday",
            columns="posted_hour",
            values="performance_score",
            aggfunc="mean",
        )
        .reindex(WEEKDAYS)
        .rename(index=WEEKDAY_LABELS)
    )
    heatmap_records = []
    for weekday_label, row in pivot.iterrows():
        for hour, value in row.items():
            if pd.notna(value):
                heatmap_records.append({"weekday": weekday_label, "hour": int(hour), "score": round(float(value), 1)})

    return {
        "available": True,
        "top_slots": _records(grouped.head(8)),
        "heatmap": heatmap_records,
        "sample_size_note": _sample_size_note(timed),
    }


def detect_patterns(
    data: pd.DataFrame,
    pillar_performance: list[dict[str, Any]],
    optimal_time: dict[str, Any],
) -> dict[str, Any]:
    if data.empty:
        return {"success_patterns": [], "failure_patterns": [], "diagnostics": {}}

    q75 = data["performance_score"].quantile(0.75)
    q25 = data["performance_score"].quantile(0.25)
    top = data[data["performance_score"] >= q75]
    bottom = data[data["performance_score"] <= q25]

    success_patterns: list[str] = []
    failure_patterns: list[str] = []

    best_pillar = pillar_performance[0] if pillar_performance else None
    if best_pillar:
        success_patterns.append(
            f"Pillar '{best_pillar['content_pillar']}' đang dẫn đầu với điểm trung bình {best_pillar['avg_score']:.1f} và {int(best_pillar['videos'])} video."
        )

    if optimal_time.get("top_slots"):
        slot = optimal_time["top_slots"][0]
        success_patterns.append(
            f"Khung giờ nổi bật nhất là {slot['slot']} với điểm trung bình {slot['avg_score']:.1f}."
        )

    top_bucket = _dominant_value(top, "duration_bucket")
    bottom_bucket = _dominant_value(bottom, "duration_bucket")
    if top_bucket:
        success_patterns.append(f"Nhóm video thắng thường rơi vào độ dài '{top_bucket}'.")
    if bottom_bucket and bottom_bucket != top_bucket:
        failure_patterns.append(f"Nhóm yếu tập trung nhiều ở độ dài '{bottom_bucket}'.")

    top_question_share = float(top["question_hook"].mean()) if not top.empty else 0
    bottom_question_share = float(bottom["question_hook"].mean()) if not bottom.empty else 0
    if top_question_share - bottom_question_share > 0.15:
        success_patterns.append("Hook dạng câu hỏi hoặc 'how-to' xuất hiện nhiều hơn trong nhóm video thắng.")
    elif bottom_question_share - top_question_share > 0.15:
        failure_patterns.append("Hook dạng câu hỏi đang chưa đủ mạnh trong nhóm video yếu; cần thử lại với promise cụ thể hơn.")

    top_hashtags = float(top["hashtag_count"].median()) if not top.empty else 0
    bottom_hashtags = float(bottom["hashtag_count"].median()) if not bottom.empty else 0
    if abs(top_hashtags - bottom_hashtags) >= 2:
        success_patterns.append(f"Nhóm thắng có median {top_hashtags:.0f} hashtag, khác rõ so với nhóm yếu {bottom_hashtags:.0f}.")

    if bottom.empty or len(data) < 8:
        failure_patterns.append("Dataset còn nhỏ; nên coi pattern như tín hiệu ban đầu, chưa phải kết luận chắc chắn.")
    else:
        weak_pillar = _dominant_value(bottom, "content_pillar")
        if weak_pillar:
            failure_patterns.append(f"Pillar '{weak_pillar}' xuất hiện nhiều trong nhóm dưới, cần rà lại angle, hook hoặc format.")

    if not success_patterns:
        success_patterns.append("Chưa có đủ khác biệt rõ giữa nhóm video top và nhóm còn lại.")

    diagnostics = {
        "top_group_size": int(len(top)),
        "bottom_group_size": int(len(bottom)),
        "top_median_score": float(top["performance_score"].median()) if not top.empty else None,
        "bottom_median_score": float(bottom["performance_score"].median()) if not bottom.empty else None,
        "top_median_views": float(top["views"].median()) if not top.empty else None,
        "bottom_median_views": float(bottom["views"].median()) if not bottom.empty else None,
    }

    return {
        "success_patterns": success_patterns,
        "failure_patterns": failure_patterns,
        "diagnostics": diagnostics,
    }


def build_growth_forecast(data: pd.DataFrame) -> dict[str, Any]:
    dated = data[data["posted_at_dt"].notna()].copy()
    if dated["posted_date"].nunique() < 2:
        return {
            "available": False,
            "outlook": "Chưa đủ dữ liệu theo thời gian để dự báo tăng trưởng.",
            "actual": [],
            "forecast": [],
            "growth_rate_pct": None,
        }

    daily = (
        dated.groupby("posted_date")
        .agg(views=("views", "sum"), followers_gained=("followers_gained", "sum"), engagements=("engagements", "sum"))
        .sort_index()
    )
    full_index = pd.date_range(daily.index.min(), daily.index.max(), freq="D").date
    daily = daily.reindex(full_index).fillna(0)

    forecast_dates = [daily.index[-1] + timedelta(days=offset) for offset in range(1, 31)]
    forecast_views = _linear_forecast(daily["views"].to_numpy(dtype=float), periods=30)
    forecast_followers = _linear_forecast(daily["followers_gained"].to_numpy(dtype=float), periods=30)
    forecast_engagements = _linear_forecast(daily["engagements"].to_numpy(dtype=float), periods=30)

    actual_last_30 = float(daily["views"].tail(30).sum())
    forecast_next_30 = float(np.sum(forecast_views))
    growth_rate = ((forecast_next_30 - actual_last_30) / actual_last_30 * 100) if actual_last_30 > 0 else None

    if growth_rate is None:
        outlook = "Dữ liệu view quá thấp để tính tốc độ tăng trưởng đáng tin cậy."
    elif growth_rate >= 20:
        outlook = f"Đà tăng trưởng tích cực, dự báo view 30 ngày tới cao hơn khoảng {growth_rate:.1f}%."
    elif growth_rate >= -10:
        outlook = f"Tăng trưởng tương đối ổn định, dự báo thay đổi khoảng {growth_rate:.1f}%."
    else:
        outlook = f"Đà tăng trưởng đang suy giảm, dự báo view 30 ngày tới giảm khoảng {abs(growth_rate):.1f}%."

    actual_frame = daily.reset_index(drop=False).rename(columns={"index": "date", "posted_date": "date"})
    actual_records = [
        {
            "date": _format_date(row["date"]),
            "views": float(row["views"]),
            "followers_gained": float(row["followers_gained"]),
            "engagements": float(row["engagements"]),
        }
        for _, row in actual_frame.iterrows()
    ]

    forecast_records = [
        {
            "date": _format_date(day),
            "views": float(max(0, forecast_views[idx])),
            "followers_gained": float(max(0, forecast_followers[idx])),
            "engagements": float(max(0, forecast_engagements[idx])),
        }
        for idx, day in enumerate(forecast_dates)
    ]

    return {
        "available": True,
        "outlook": outlook,
        "actual": actual_records,
        "forecast": forecast_records,
        "growth_rate_pct": growth_rate,
        "forecast_next_30_views": forecast_next_30,
        "actual_last_30_views": actual_last_30,
    }


def build_content_calendar(
    data: pd.DataFrame,
    pillar_performance: list[dict[str, Any]],
    optimal_time: dict[str, Any],
) -> dict[str, Any]:
    if data["posted_at_dt"].notna().any():
        reference = data["posted_at_dt"].max().date()
    else:
        reference = datetime.now().date()

    if reference.month == 12:
        month_start = date(reference.year + 1, 1, 1)
    else:
        month_start = date(reference.year, reference.month + 1, 1)

    days_in_month = calendar_lib.monthrange(month_start.year, month_start.month)[1]
    month_end = date(month_start.year, month_start.month, days_in_month)

    posts_per_month = _estimate_posts_per_month(data)
    posts_per_month = int(np.clip(posts_per_month, 8, 24))

    pillars = [item["content_pillar"] for item in pillar_performance[:5]] or ["Education", "Community", "Product"]
    slots = _calendar_slots(optimal_time)
    platform = _dominant_value(data, "platform") or "TikTok / YouTube / Facebook"

    calendar_items: list[dict[str, Any]] = []
    used_dates: set[date] = set()
    for idx in range(posts_per_month):
        slot = slots[idx % len(slots)]
        raw_day = month_start + timedelta(days=round(idx * max(1, days_in_month - 1) / max(1, posts_per_month - 1)))
        publish_day = _nearest_weekday_in_month(raw_day, slot["weekday_num"], month_start, month_end, used_dates)
        used_dates.add(publish_day)

        pillar = pillars[idx % len(pillars)]
        content_format, hook, goal, kpi = _calendar_idea(pillar, idx)
        calendar_items.append(
            {
                "date": publish_day.isoformat(),
                "time": f"{slot['hour']:02d}:00",
                "weekday": WEEKDAY_LABELS[WEEKDAYS[publish_day.weekday()]],
                "platform": platform,
                "pillar": pillar,
                "format": content_format,
                "hook": hook,
                "goal": goal,
                "primary_kpi": kpi,
            }
        )

    return {
        "month": month_start.strftime("%Y-%m"),
        "recommended_posts": posts_per_month,
        "strategy": [
            f"Ưu tiên 3-5 pillar có điểm hiệu suất cao nhất: {', '.join(pillars[:5])}.",
            "Lặp lại khung giờ thắng, nhưng giữ 20-30% slot cho thử nghiệm format mới.",
            "Mỗi tuần nên có ít nhất một nội dung depth/education và một nội dung community/trend để cân bằng reach và trust.",
        ],
        "items": sorted(calendar_items, key=lambda item: (item["date"], item["time"])),
    }


def build_summary(
    prepared: pd.DataFrame,
    pillar_performance: list[dict[str, Any]],
    optimal_time: dict[str, Any],
    forecast: dict[str, Any],
    content_calendar: dict[str, Any],
) -> dict[str, Any]:
    best_video = prepared.sort_values("performance_score", ascending=False).iloc[0]
    best_pillar = pillar_performance[0] if pillar_performance else None
    best_slot = optimal_time.get("top_slots", [None])[0] if optimal_time.get("top_slots") else None
    date_values = prepared["posted_at_dt"].dropna()

    if not date_values.empty:
        date_range = f"{date_values.min().date().isoformat()} đến {date_values.max().date().isoformat()}"
    else:
        date_range = "Không có ngày đăng hợp lệ"

    return {
        "total_videos": int(len(prepared)),
        "date_range": date_range,
        "total_views": float(prepared["views"].sum()),
        "total_engagements": float(prepared["engagements"].sum()),
        "avg_engagement_rate": float(prepared["engagement_rate"].mean()),
        "avg_performance_score": float(prepared["performance_score"].mean()),
        "best_video": {
            "title": str(best_video["title"]),
            "score": float(best_video["performance_score"]),
            "views": float(best_video["views"]),
            "pillar": str(best_video["content_pillar"]),
        },
        "best_pillar": best_pillar,
        "best_slot": best_slot,
        "growth_outlook": forecast.get("outlook"),
        "next_calendar_month": content_calendar.get("month"),
        "recommended_posts": content_calendar.get("recommended_posts"),
    }


def build_dashboard_charts(
    data: pd.DataFrame,
    pillar_performance: list[dict[str, Any]],
    optimal_time: dict[str, Any],
    forecast: dict[str, Any],
) -> dict[str, Any]:
    top = data.sort_values("performance_score", ascending=False).head(10).iloc[::-1]
    top_fig = go.Figure(
        data=[
            go.Bar(
                x=top["performance_score"],
                y=top["title"].map(lambda value: _truncate(str(value), 42)),
                orientation="h",
                marker_color="#0f766e",
                hovertemplate="%{y}<br>Score: %{x:.1f}<extra></extra>",
            )
        ]
    )
    top_fig.update_layout(title="Top video theo performance score", xaxis_title="Score", yaxis_title="")

    pillar_df = pd.DataFrame(pillar_performance)
    pillar_fig = go.Figure()
    if not pillar_df.empty:
        pillar_fig.add_bar(
            x=pillar_df["content_pillar"],
            y=pillar_df["avg_score"],
            marker_color="#2563eb",
            hovertemplate="%{x}<br>Score: %{y:.1f}<extra></extra>",
        )
    pillar_fig.update_layout(title="Hiệu suất theo content pillar", xaxis_title="", yaxis_title="Avg score")

    heatmap_fig = go.Figure()
    heatmap_records = optimal_time.get("heatmap", [])
    if heatmap_records:
        heatmap_df = pd.DataFrame(heatmap_records)
        pivot = heatmap_df.pivot_table(index="weekday", columns="hour", values="score", aggfunc="mean")
        pivot = pivot.reindex(["T2", "T3", "T4", "T5", "T6", "T7", "CN"])
        heatmap_fig.add_trace(
            go.Heatmap(
                z=pivot.to_numpy(),
                x=[f"{int(hour):02d}:00" for hour in pivot.columns],
                y=pivot.index.tolist(),
                colorscale="Teal",
                hoverongaps=False,
                colorbar={"title": "Score"},
            )
        )
    else:
        heatmap_fig.add_annotation(text="Chưa có dữ liệu ngày/giờ đăng", showarrow=False)
    heatmap_fig.update_layout(title="Bản đồ hiệu suất theo giờ đăng", xaxis_title="Giờ", yaxis_title="Thứ")

    forecast_fig = go.Figure()
    if forecast.get("available"):
        actual = pd.DataFrame(forecast["actual"])
        predicted = pd.DataFrame(forecast["forecast"])
        forecast_fig.add_trace(
            go.Scatter(x=actual["date"], y=actual["views"], mode="lines", name="Actual views", line={"color": "#1f2937"})
        )
        forecast_fig.add_trace(
            go.Scatter(
                x=predicted["date"],
                y=predicted["views"],
                mode="lines",
                name="Forecast views",
                line={"color": "#dc2626", "dash": "dash"},
            )
        )
    else:
        forecast_fig.add_annotation(text=forecast.get("outlook", "Chưa đủ dữ liệu dự báo"), showarrow=False)
    forecast_fig.update_layout(title="Dự báo tăng trưởng view 30 ngày", xaxis_title="", yaxis_title="Views")

    scatter_fig = go.Figure(
        data=[
            go.Scatter(
                x=data["views"],
                y=data["engagement_rate"],
                text=data["title"].map(lambda value: _truncate(str(value), 64)),
                mode="markers",
                marker={
                    "size": (data["performance_score"].clip(10, 100) / 4).tolist(),
                    "color": data["performance_score"],
                    "colorscale": "Viridis",
                    "showscale": True,
                    "colorbar": {"title": "Score"},
                    "line": {"width": 0.5, "color": "#ffffff"},
                },
                hovertemplate="%{text}<br>Views: %{x:,.0f}<br>ER: %{y:.2f}%<extra></extra>",
            )
        ]
    )
    scatter_fig.update_layout(title="Views vs engagement rate", xaxis_title="Views", yaxis_title="Engagement rate (%)")

    return {
        "top_videos": _fig_json(top_fig),
        "pillar_performance": _fig_json(pillar_fig),
        "posting_time_heatmap": _fig_json(heatmap_fig),
        "growth_forecast": _fig_json(forecast_fig),
        "engagement_scatter": _fig_json(scatter_fig),
    }


def compute_performance_score(data: pd.DataFrame) -> pd.Series:
    metrics = {
        "views": (data["views"], 0.30),
        "engagement_rate": (data["engagement_rate"], 0.25),
        "shares_per_1k_views": (data["shares_per_1k_views"], 0.15),
        "saves_per_1k_views": (data["saves_per_1k_views"], 0.10),
        "followers_per_1k_views": (data["followers_per_1k_views"], 0.10),
        "completion_rate": (data["completion_rate"], 0.10),
    }

    score = pd.Series(0.0, index=data.index)
    total_weight = 0.0
    for series, weight in metrics.values():
        clean = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
        if clean.notna().sum() == 0:
            continue
        score += _percentile_score(clean) * weight
        total_weight += weight

    if total_weight == 0:
        return pd.Series(50.0, index=data.index)

    score = (score / total_weight).clip(0, 100).round(1)
    return score


def infer_content_pillar(title: Any) -> str:
    text = str(title or "").lower()
    rules = [
        ("Education", ["how", "guide", "tips", "tutorial", "cách", "hướng dẫn", "mẹo", "bước"]),
        ("Trend / Viral", ["trend", "challenge", "viral", "reaction", "duet", "remix", "hot"]),
        ("Product / Offer", ["product", "demo", "review", "launch", "sale", "deal", "sản phẩm", "ưu đãi"]),
        ("Authority / Thought Leadership", ["case study", "insight", "framework", "strategy", "phân tích", "chiến lược"]),
        ("Community / Story", ["story", "behind", "day in", "journey", "team", "khách hàng", "câu chuyện"]),
        ("Entertainment", ["funny", "meme", "fail", "skit", "hài", "giải trí"]),
    ]
    for pillar, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return pillar
    return "Uncategorized"


def _build_posted_datetime(
    raw: pd.DataFrame,
    lookup: dict[str, str],
    field_map: dict[str, str],
    fallback: pd.Series,
) -> pd.Series:
    date_col = _find_column(lookup, POSTED_DATE_SYNONYMS)
    time_col = _find_column(lookup, POSTED_TIME_SYNONYMS)

    if date_col and time_col and date_col != time_col:
        date_part = raw[date_col].map(_date_text_for_parse)
        time_part = raw[time_col].map(_time_text_for_parse)
        combined = (date_part + " " + time_part).str.strip()
        combined_dt = pd.to_datetime(combined, errors="coerce")

        if combined_dt.notna().any():
            field_map["posted_at"] = f"{date_col} + {time_col}"
            field_map["posted_date"] = date_col
            field_map["posted_time"] = time_col
            return combined_dt

    if date_col:
        date_dt = pd.to_datetime(raw[date_col], errors="coerce")
        if date_dt.notna().any():
            field_map["posted_at"] = date_col
            field_map["posted_date"] = date_col
            return date_dt

    return pd.to_datetime(fallback, errors="coerce")


def _date_text_for_parse(value: Any) -> str:
    if _is_missing_scalar(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.notna(parsed):
        return parsed.date().isoformat()
    return text


def _time_text_for_parse(value: Any) -> str:
    if _is_missing_scalar(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.time().strftime("%H:%M:%S")
    if isinstance(value, datetime):
        return value.time().strftime("%H:%M:%S")
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, (int, float, np.integer, np.floating)):
        numeric = float(value)
        if 0 <= numeric < 1:
            total_seconds = int(round(numeric * 24 * 60 * 60))
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    text = str(value).strip()
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.notna(parsed):
        return parsed.time().strftime("%H:%M:%S")
    return text


def _is_missing_scalar(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _find_column(lookup: dict[str, str], synonyms: list[str]) -> str | None:
    for synonym in synonyms:
        key = _canonicalize(synonym)
        if key in lookup:
            return lookup[key]

    for key, source in lookup.items():
        for synonym in synonyms:
            canonical = _canonicalize(synonym)
            if len(canonical) < 4:
                continue
            if key.endswith(canonical) or canonical in key:
                return source
    return None


def _canonicalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _not_blank(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "")


def _to_numeric_series(series: pd.Series) -> pd.Series:
    return series.map(_parse_number).astype(float)


def _parse_number(value: Any) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip().lower()
    if text in {"", "-", "nan", "none", "n/a", "null"}:
        return np.nan

    multiplier = 1.0
    percent = text.endswith("%")
    text = text.replace("%", "").replace(",", "")
    if text.endswith("k"):
        multiplier = 1_000.0
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000.0
        text = text[:-1]
    elif text.endswith("b"):
        multiplier = 1_000_000_000.0
        text = text[:-1]

    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", "."}:
        return np.nan
    try:
        parsed = float(text) * multiplier
    except ValueError:
        return np.nan
    return parsed if not percent else parsed


def _parse_duration_seconds(value: Any) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip().lower()
    if text in {"", "-", "nan", "none", "n/a"}:
        return np.nan

    colon_match = re.fullmatch(r"(?:(\d+):)?(\d{1,2}):(\d{2})", text)
    if colon_match:
        hours = int(colon_match.group(1) or 0)
        minutes = int(colon_match.group(2))
        seconds = int(colon_match.group(3))
        return float(hours * 3600 + minutes * 60 + seconds)

    short_match = re.search(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?", text)
    if short_match and any(short_match.groups()):
        hours = int(short_match.group(1) or 0)
        minutes = int(short_match.group(2) or 0)
        seconds = int(short_match.group(3) or 0)
        return float(hours * 3600 + minutes * 60 + seconds)

    return _parse_number(value)


def _normalize_rate_percent(series: pd.Series) -> pd.Series:
    values = _to_numeric_series(series)
    valid = values.dropna()
    if not valid.empty and valid.quantile(0.9) <= 1.5:
        values = values * 100
    return values


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    result = numerator / denominator
    return result.replace([np.inf, -np.inf], np.nan).fillna(0)


def _percentile_score(series: pd.Series) -> pd.Series:
    clean = series.replace([np.inf, -np.inf], np.nan)
    if clean.nunique(dropna=True) <= 1:
        return pd.Series(50.0, index=series.index)
    return (clean.rank(pct=True) * 100).fillna(0)


def _duration_bucket(seconds: Any) -> str:
    value = float(seconds or 0)
    if value <= 0:
        return "Unknown"
    if value < 30:
        return "Short <30s"
    if value <= 90:
        return "Medium 30-90s"
    if value <= 300:
        return "Long 1.5-5m"
    return "Deep >5m"


def _tier_from_score(score: float) -> str:
    if score >= 80:
        return "Top performer"
    if score >= 65:
        return "Strong"
    if score >= 45:
        return "Average"
    return "Underperforming"


def _sample_size_note(data: pd.DataFrame) -> str:
    if len(data) < 12:
        return "Mẫu dữ liệu còn nhỏ; khung giờ nên được kiểm chứng thêm."
    return "Khung giờ được xếp hạng theo score trung bình và median views."


def _dominant_value(data: pd.DataFrame, column: str) -> str | None:
    if data.empty or column not in data:
        return None
    counts = data[column].dropna().astype(str)
    counts = counts[counts.str.strip() != ""]
    if counts.empty:
        return None
    return counts.value_counts().index[0]


def _linear_forecast(values: np.ndarray, periods: int) -> np.ndarray:
    values = np.nan_to_num(values.astype(float), nan=0.0, posinf=0.0, neginf=0.0)
    if len(values) < 2:
        return np.repeat(values[-1] if len(values) else 0.0, periods)
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values, deg=1)
    future_x = np.arange(len(values), len(values) + periods, dtype=float)
    forecast = intercept + slope * future_x
    trailing_mean = float(np.mean(values[-min(7, len(values)) :]))
    forecast = forecast * 0.65 + trailing_mean * 0.35
    return np.clip(forecast, 0, None)


def _estimate_posts_per_month(data: pd.DataFrame) -> int:
    if data["posted_at_dt"].notna().sum() < 2:
        return 16
    first = data["posted_at_dt"].min().date()
    last = data["posted_at_dt"].max().date()
    active_days = max(1, (last - first).days + 1)
    monthly_rate = len(data) / active_days * 30
    if monthly_rate < 8:
        return 12
    return int(round(monthly_rate))


def _calendar_slots(optimal_time: dict[str, Any]) -> list[dict[str, int]]:
    slots = []
    for item in optimal_time.get("top_slots", [])[:4]:
        weekday_num = VI_WEEKDAY_TO_NUM.get(str(item.get("posted_weekday_label") or "").strip())
        hour = item.get("posted_hour")
        if weekday_num is not None and hour is not None:
            slots.append({"weekday_num": int(weekday_num), "hour": int(hour)})
    if slots:
        return slots
    return [
        {"weekday_num": 1, "hour": 19},
        {"weekday_num": 3, "hour": 20},
        {"weekday_num": 5, "hour": 10},
        {"weekday_num": 6, "hour": 19},
    ]


def _nearest_weekday_in_month(
    target: date,
    weekday_num: int,
    month_start: date,
    month_end: date,
    used_dates: set[date],
) -> date:
    candidates: list[date] = []
    for offset in range(-3, 4):
        candidate = target + timedelta(days=offset)
        if month_start <= candidate <= month_end and candidate.weekday() == weekday_num:
            candidates.append(candidate)
    if not candidates:
        delta = (weekday_num - target.weekday()) % 7
        candidate = target + timedelta(days=delta)
        if candidate > month_end:
            candidate = target - timedelta(days=(target.weekday() - weekday_num) % 7)
        candidates.append(max(month_start, min(month_end, candidate)))
    for candidate in sorted(candidates, key=lambda day: abs((day - target).days)):
        if candidate not in used_dates:
            return candidate
    return sorted(candidates, key=lambda day: abs((day - target).days))[0]


def _calendar_idea(pillar: str, idx: int) -> tuple[str, str, str, str]:
    pillar_lower = pillar.lower()
    if "education" in pillar_lower or "authority" in pillar_lower:
        ideas = [
            ("How-to breakdown", f"3 điều người xem thường hiểu sai về {pillar}", "Build trust", "Saves + completion"),
            ("Case teardown", f"Phân tích một ví dụ thật trong {pillar}", "Depth engagement", "Comments + avg watch"),
        ]
    elif "product" in pillar_lower:
        ideas = [
            ("Demo / proof", f"Cho thấy kết quả trước-sau của {pillar}", "Conversion intent", "CTR + followers"),
            ("FAQ clip", f"Trả lời phản đối phổ biến nhất về {pillar}", "Reduce friction", "Comments + saves"),
        ]
    elif "trend" in pillar_lower or "entertainment" in pillar_lower:
        ideas = [
            ("Trend remix", f"Gắn trend hiện tại với góc nhìn riêng của kênh", "Reach", "Views + shares"),
            ("Fast reaction", f"Phản ứng nhanh với một tín hiệu đang hot", "Discovery", "Shares + ER"),
        ]
    else:
        ideas = [
            ("Story-led post", f"Mở bằng một tình huống cụ thể trong {pillar}", "Relatability", "Comments + watch time"),
            ("Community prompt", f"Hỏi cộng đồng chọn giữa 2 quan điểm về {pillar}", "Engagement", "Comments + shares"),
        ]
    return ideas[idx % len(ideas)]


def _format_datetime(value: Any) -> str | None:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _format_date(value: Any) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _truncate(value: str, length: int) -> str:
    return value if len(value) <= length else value[: length - 1] + "…"


def _fig_json(fig: go.Figure) -> dict[str, Any]:
    fig.update_layout(
        template="plotly_white",
        margin={"l": 56, "r": 24, "t": 58, "b": 48},
        font={"family": "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        hoverlabel={"font_size": 12},
    )
    return json.loads(pio.to_json(fig, validate=False))


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [_json_ready(record) for record in df.replace({np.nan: None}).to_dict(orient="records")]


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if math.isnan(float(value)) or math.isinf(float(value)):
            return None
        return float(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, (list, dict, tuple, str, bytes)):
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
    return value
