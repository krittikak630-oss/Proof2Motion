import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

EVIDENCE = (
    "Complaint log: Eleven households have now filed written complaints with the ward office.\n"
    "Inspection report: iron levels were above the permitted limit in three of the four samples.\n"
)


def payload(**overrides):
    data = {
        "title": "Test case",
        "summary": "A short summary.",
        "claims": [
            {"claim": "Many households complained.", "status": "supported",
             "support": [{"file": "a.txt", "quote": "Eleven households have now filed written complaints", "page": None}]},
            {"claim": "Water is safe.", "status": "supported",
             "support": [{"file": "a.txt", "quote": "This sentence was invented by the model", "page": None}]},
        ],
        "gaps": ["No re-test."],
        "storyboard": [{"scene": i, "title": f"S{i}", "narration": "n", "visual": "v", "on_screen_text": "t", "duration_sec": 5} for i in range(1, 6)],
    }
    data.update(overrides)
    return json.dumps(data)


class FakeLLM:
    def __init__(self, text=None, ready=True):
        self.text, self.ready = text or payload(), ready

    def stream(self, prompt):
        yield ("progress", 10)
        yield ("done", self.text, "gemma-4-31b-it")

    def generate(self, prompt):
        return self.text, "gemma-4-31b-it"


@pytest.fixture
def make_client(tmp_path):
    (tmp_path / "index.html").write_text("<html>app</html>")

    def factory(llm=None, **settings):
        base = Settings(api_key="k", rate_limit_per_minute=100, dist_dir=tmp_path)
        return TestClient(create_app(replace(base, **settings), llm or FakeLLM()))

    return factory


@pytest.fixture
def client(make_client):
    return make_client()


def upload(name="a.txt", content=EVIDENCE.encode(), mime="text/plain"):
    return [("files", (name, content, mime))]
