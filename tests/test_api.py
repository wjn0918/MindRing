import os
from datetime import UTC, datetime

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_core_mvp_flow() -> None:
    with TestClient(app) as client:
        concept_response = client.post(
            "/api/concepts",
            json={"name": "第一性原理", "creator_id": "user_1", "description": "拆解到基本事实"},
        )
        assert concept_response.status_code == 201
        concept_id = concept_response.json()["id"]

        first_response = client.post(
            "/api/insights",
            json={
                "concept_id": concept_id,
                "author_id": "user_1",
                "content": "从基本事实重新推导，而不是类比。",
                "mood": "清醒",
                "tags": ["思维模型"],
                "occurred_at": datetime(2025, 1, 1, tzinfo=UTC).isoformat(),
            },
        )
        assert first_response.status_code == 201
        first_id = first_response.json()["id"]
        assert first_response.json()["previous_insight"] is None

        second_response = client.post(
            "/api/insights",
            json={
                "concept_id": concept_id,
                "author_id": "user_1",
                "content": "先识别不可再分的事实，再承认约束和代价。",
                "mood": "笃定",
                "tags": ["思维模型", "复盘"],
                "occurred_at": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
            },
        )
        assert second_response.status_code == 201
        second_body = second_response.json()
        assert second_body["previous_insight"]["id"] == first_id

        timeline_response = client.get(f"/api/concepts/{concept_id}/timeline?order=asc")
        assert timeline_response.status_code == 200
        assert [item["id"] for item in timeline_response.json()] == [first_id, second_body["id"]]

        diff_response = client.get(
            f"/api/insights/diff?left_id={first_id}&right_id={second_body['id']}"
        )
        assert diff_response.status_code == 200
        assert diff_response.json()["added_lines"] == ["先识别不可再分的事实，再承认约束和代价。"]

        calendar_response = client.get("/api/calendar?user_id=user_1")
        assert calendar_response.status_code == 200
        assert calendar_response.json() == [
            {"date": "2025-01-01", "count": 1},
            {"date": "2026-01-01", "count": 1},
        ]
