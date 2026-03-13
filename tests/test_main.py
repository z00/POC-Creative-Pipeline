import json
import os
import shutil
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pipeline import CAMPAIGN_DB

client = TestClient(app)


@pytest.fixture(autouse=True)
def run_around_tests():
    """Before each test, clear DB. After each test, clear DB and storage."""
    CAMPAIGN_DB.clear()
    yield
    # Cleanup logic
    CAMPAIGN_DB.clear()
    for subfolder in ["inputs", "outputs"]:
        path = os.path.join("storage", subfolder)
        if os.path.exists(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.unlink(item_path)


def test_campaign_lifecycle():
    payload = {
        "campaign_name": "Lifecycle Test",
        "target_region": "US",
        "target_audience": "All",
        "campaign_message": "Hello",
        "products": [
            {"id": "1", "name": "P1", "description": "D1"},
            {"id": "2", "name": "P2", "description": "D2"},
        ],
    }

    # We patch the BACKGROUND task so the test stays fast
    with patch("app.main.pipeline.process_campaign") as mocked_proc:
        # 1. TEST CREATION
        create_res = client.post(
            "/campaigns/", data={"campaign_data": json.dumps(payload)}
        )
        assert create_res.status_code == 200
        campaign_id = create_res.json()["id"]

        # Confirm the AI wasn't actually called, just scheduled
        mocked_proc.assert_called_once()

        # 2. TEST EXISTENCE
        get_res = client.get(f"/campaigns/{campaign_id}")
        assert get_res.status_code == 200
        assert get_res.json()["status"] == "queued"

        # 3. TEST DELETION
        del_res = client.delete(f"/campaigns/{campaign_id}")
        assert del_res.status_code == 200

        # 4. TEST NON-EXISTENCE
        final_get = client.get(f"/campaigns/{campaign_id}")
        assert final_get.status_code == 404
