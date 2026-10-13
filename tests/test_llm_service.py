
import pytest
from unittest.mock import MagicMock, patch

from services.llm_service import analyze_requirement


def test_empty_requirement_raises_value_error():
    with pytest.raises(ValueError, match="Requirement text is empty"):
        analyze_requirement("")


def test_whitespace_requirement_raises_value_error():
    with pytest.raises(ValueError, match="Requirement text is empty"):
        analyze_requirement("   ")


def test_missing_api_key_raises_runtime_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        analyze_requirement("As a user, I can log in.")




def test_successful_analysis_returns_gemini_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

    mock_response = MagicMock()
    mock_response.text = "Risk Score: 3/10"

    with patch("services.llm_service.genai.GenerativeModel") as mock_model_class:
        mock_model = mock_model_class.return_value
        mock_model.generate_content.return_value = mock_response

        result = analyze_requirement("As a user, I can log in.")

    assert result == "Risk Score: 3/10"
    mock_model.generate_content.assert_called_once()



def test_gemini_failure_raises_runtime_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

    with patch("services.llm_service.genai.GenerativeModel") as mock_model_class:
        mock_model_class.side_effect = Exception("Simulated setup failure")

        with pytest.raises(RuntimeError, match="Gemini analysis failed"):
            analyze_requirement("As a user, I can log in.")


def test_empty_gemini_response_raises_runtime_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")

    mock_response = MagicMock()
    mock_response.text = "   "

    with patch("services.llm_service.genai.GenerativeModel") as mock_model_class:
        mock_model = mock_model_class.return_value
        mock_model.generate_content.return_value = mock_response

        with pytest.raises(RuntimeError, match="Gemini returned an empty response"):
            analyze_requirement("As a user, I can log in.")
