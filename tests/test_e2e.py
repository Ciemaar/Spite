from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from spite.main import app

client = TestClient(app)


@pytest.fixture
def mock_ingestor():
    with patch("spite.ingest.IngestionManager") as MockIngestor:
        instance = MockIngestor.return_value
        instance.ingest_github_repo = AsyncMock(
            return_value={"README.md": "# Fake Repo"}
        )
        instance.fetch_urls = AsyncMock(return_value={})
        instance.search_web = MagicMock(return_value="")
        instance.close = AsyncMock()
        yield instance


@pytest.fixture
def mock_dspy_config():
    with patch("spite.llm.configure_dspy") as MockConfigure:
        yield MockConfigure


def test_process_phase_1(mock_ingestor, mock_dspy_config):
    mock_specs = {
        "REQUIREMENTS.md": "Fake reqs",
        "IMPLEMENTATION_PLAN.md": "Fake plan",
        "AGENTS.md": "Fake instructions",
        "TESTING.md": "Fake testing",
        "IMPROVEMENTS.md": "Fake improvements",
        "DIRTY_BIBLIOGRAPHY.md": "Fake bibliography",
        "SYSTEM_OVERVIEW.md": "Fake overview",
        "SOURCE_EXCLUDES.txt": "Fake excludes",
    }

    with patch("spite.analyzer.DirtyAgent") as MockDirty:
        dirty_instance = MockDirty.return_value
        dirty_instance.analyze = AsyncMock(return_value=mock_specs)

        response = client.post(
            "/process",
            data={
                "github_url": "https://github.com/fake/repo",
                "ai_provider": "ollama",
                "ai_model": "llama3",
                "target_phase": "1",
                "client_id": "test-client-id",
                "supplemental_urls": "",
                "web_search": False,
                "additional_instructions": "",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Phase 1 Complete" in response.text
        assert "Download .zip" in response.text
        assert len(response.content) > 0


def test_process_phase_2(mock_ingestor, mock_dspy_config):
    # Mock Dirty Agent output
    mock_specs = {
        "REQUIREMENTS.md": "Fake reqs",
        "IMPLEMENTATION_PLAN.md": "Fake plan",
        "AGENTS.md": "Fake instructions",
        "TESTING.md": "Fake testing",
        "IMPROVEMENTS.md": "Fake improvements",
        "DIRTY_BIBLIOGRAPHY.md": "Fake bibliography",
        "SYSTEM_OVERVIEW.md": "Fake overview",
        "SOURCE_EXCLUDES.txt": "Fake excludes",
    }

    with patch("spite.analyzer.DirtyAgent") as MockDirty:
        dirty_instance = MockDirty.return_value
        dirty_instance.analyze = AsyncMock(return_value=mock_specs)

        with patch("spite.generator.CleanAgent") as MockClean:
            clean_instance = MockClean.return_value
            clean_instance.generate_codebase = AsyncMock()
            clean_instance.apply_improvements = AsyncMock()

            with patch("spite.packager.init_local_repo") as mock_init:
                mock_init.return_value = "/tmp/fake_repo"

                with patch("subprocess.run"):
                    response = client.post(
                        "/process",
                        data={
                            "github_url": "https://github.com/fake/repo",
                            "ai_provider": "ollama",
                            "ai_model": "llama3",
                            "target_phase": "2",
                            "client_id": "test-client-id",
                            "supplemental_urls": "",
                            "web_search": False,
                            "additional_instructions": "Do a good job.",
                        },
                    )

                    assert response.status_code == 200
                    assert "Phase 2 Complete" in response.text
                    assert "/tmp/fake_repo" in response.text

                    # Verify CleanAgent was called
                    clean_instance.generate_codebase.assert_called_once()

                    # Verify instructions were injected
                    called_specs = clean_instance.generate_codebase.call_args[0][0]
                    assert "Additional Instructions" in called_specs["AGENTS.md"]
                    assert "Do a good job." in called_specs["AGENTS.md"]


def test_process_phase_3(mock_ingestor, mock_dspy_config):
    mock_specs = {
        "REQUIREMENTS.md": "Fake reqs",
        "IMPLEMENTATION_PLAN.md": "Fake plan",
        "AGENTS.md": "Fake instructions",
        "TESTING.md": "Fake testing",
        "IMPROVEMENTS.md": "Fake improvements",
        "DIRTY_BIBLIOGRAPHY.md": "Fake bibliography",
        "SYSTEM_OVERVIEW.md": "Fake overview",
        "SOURCE_EXCLUDES.txt": "Fake excludes",
    }

    with patch("spite.analyzer.DirtyAgent") as MockDirty:
        dirty_instance = MockDirty.return_value
        dirty_instance.analyze = AsyncMock(return_value=mock_specs)

        with patch("spite.generator.CleanAgent") as MockClean:
            clean_instance = MockClean.return_value
            clean_instance.generate_codebase = AsyncMock()
            clean_instance.apply_improvements = AsyncMock()

            with patch("spite.packager.init_local_repo") as mock_init:
                mock_init.return_value = "/tmp/fake_repo"

                with patch("subprocess.run"):
                    response = client.post(
                        "/process",
                        data={
                            "github_url": "https://github.com/fake/repo",
                            "ai_provider": "ollama",
                            "ai_model": "llama3",
                            "target_phase": "3",
                            "client_id": "test-client-id",
                            "supplemental_urls": "",
                            "web_search": False,
                            "additional_instructions": "",
                        },
                    )

                    assert response.status_code == 200
                    assert "Phase 3 Complete" in response.text
                    clean_instance.apply_improvements.assert_called_once()
