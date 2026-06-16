from pathlib import Path

import pandas as pd

from app.analysis import analyze_video_dataframe


def test_analysis_generates_core_sections():
    sample_path = Path(__file__).resolve().parents[1] / "sample_data" / "content_performance_sample.csv"
    df = pd.read_csv(sample_path)

    result = analyze_video_dataframe(df)

    assert result["summary"]["total_videos"] == 20
    assert result["summary"]["best_video"]["score"] > 0
    assert result["pillar_performance"]
    assert result["optimal_time"]["top_slots"]
    assert result["growth_forecast"]["available"] is True
    assert result["content_calendar"]["items"]
    assert "top_videos" in result["charts"]


def test_analysis_accepts_channel_dataset_column_names():
    df = pd.DataFrame(
        [
            {
                "Video ID": "v001",
                "Title caption": "How to plan content faster",
                "Post date": "2026-05-01",
                "Post time": "19:00",
                "Content pillar": "Education",
                "Views": 1000,
                "Like": 120,
                "Comment": 20,
                "Share": 10,
                "Saves": 30,
                "Followers_gained": 12,
                "Avg Watch Time (s)": 45,
                "Avg Watch %": "75%",
                "Video Duration (s)": 60,
            },
            {
                "Video ID": "v002",
                "Title caption": "Behind the scenes",
                "Post date": "2026-05-02",
                "Post time": "09:30",
                "Content pillar": "Community",
                "Views": 500,
                "Like": 30,
                "Comment": 5,
                "Share": 2,
                "Saves": 4,
                "Followers_gained": 3,
                "Avg Watch Time (s)": 20,
                "Avg Watch %": "50%",
                "Video Duration (s)": 40,
            },
        ]
    )

    result = analyze_video_dataframe(df)

    assert result["schema"]["field_map"]["posted_at"] == "Post date + Post time"
    assert result["schema"]["field_map"]["likes"] == "Like"
    assert result["schema"]["field_map"]["comments"] == "Comment"
    assert result["schema"]["field_map"]["shares"] == "Share"
    assert result["schema"]["field_map"]["retention_rate"] == "Avg Watch %"
    assert result["summary"]["date_range"].startswith("2026-05-01")
    assert result["summary"]["date_range"].endswith("2026-05-02")
    assert result["summary"]["total_engagements"] == 221.0
    assert result["per_video"][0]["posted_at"].startswith("2026-05-01T19:00:00")
