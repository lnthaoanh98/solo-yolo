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

