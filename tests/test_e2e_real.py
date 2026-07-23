import os

import pytest
from fastapi.testclient import TestClient

from spite.main import app

client = TestClient(app)

@pytest.mark.skipif(
    not os.environ.get("SPITE_RUN_REAL_E2E"),
    reason="SPITE_RUN_REAL_E2E environment variable not set",
)
def test_real_process_phase_2():
    """Real End-to-End test that calls the GitHub API and Ollama.

    Warning: This test will be slow and requires Ollama running locally.
    We target a very small repo to minimize context window and generation time.
    """
    response = client.post(
        "/process",
        data={
            "github_url": "https://github.com/octocat/Hello-World",
            "ai_provider": "ollama",
            "ai_model": "llama3",  # Assuming llama3 is pulled locally
            "target_phase": "2",
            "supplemental_urls": "",
            "web_search": False,
            "additional_instructions": "Make it simple.",
        },
        timeout=300.0, # LLMs can take a long time
    )

    assert response.status_code == 200
    assert "Phase 2 Complete" in response.text
    assert "Repository implemented at:" in response.text
