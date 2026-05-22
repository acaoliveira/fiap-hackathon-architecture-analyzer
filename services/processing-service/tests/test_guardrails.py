import json
import pytest
from pathlib import Path
import tempfile

from src.infrastructure.ai.guardrails import (
    InputValidationError,
    OutputValidationError,
    validate_and_sanitize_output,
    validate_input_file,
)


def test_validate_output_valid():
    raw = json.dumps(
        {
            "summary": "A simple microservice architecture.",
            "components": [{"name": "API Gateway", "type": "gateway", "description": "Entry point"}],
            "architectural_risks": [{"severity": "high", "title": "No auth", "description": "Missing authentication"}],
            "recommendations": [{"priority": "high", "title": "Add auth", "action": "Implement OAuth2"}],
        }
    )
    result = validate_and_sanitize_output(raw)
    assert result["summary"] == "A simple microservice architecture."
    assert len(result["components"]) == 1
    assert result["components"][0]["type"] == "gateway"


def test_validate_output_sanitizes_unknown_component_type():
    raw = json.dumps(
        {
            "summary": "Test",
            "components": [{"name": "X", "type": "blockchain_node", "description": "Some thing"}],
            "architectural_risks": [],
            "recommendations": [],
        }
    )
    result = validate_and_sanitize_output(raw)
    assert result["components"][0]["type"] == "other"


def test_validate_output_rejects_non_architecture():
    raw = json.dumps({"error": "not_architecture_diagram"})
    with pytest.raises(OutputValidationError):
        validate_and_sanitize_output(raw)


def test_validate_output_rejects_invalid_json():
    with pytest.raises(OutputValidationError):
        validate_and_sanitize_output("this is not json")


def test_validate_output_rejects_missing_components():
    raw = json.dumps({"summary": "ok", "components": [], "architectural_risks": [], "recommendations": []})
    with pytest.raises(OutputValidationError):
        validate_and_sanitize_output(raw)


def test_validate_output_truncates_long_fields():
    long_text = "x" * 1000
    raw = json.dumps(
        {
            "summary": long_text,
            "components": [{"name": "A", "type": "service", "description": long_text}],
            "architectural_risks": [],
            "recommendations": [],
        }
    )
    result = validate_and_sanitize_output(raw)
    assert len(result["summary"]) <= 400
    assert len(result["components"][0]["description"]) <= 400


def test_validate_input_file_not_found():
    with pytest.raises(InputValidationError, match="not found"):
        validate_input_file("/nonexistent/file.png", "image/png")


def test_validate_input_file_disallowed_type():
    with tempfile.NamedTemporaryFile(suffix=".exe") as f:
        f.write(b"MZ...")
        f.flush()
        with pytest.raises(InputValidationError, match="Disallowed"):
            validate_input_file(f.name, "application/octet-stream")


def test_validate_input_file_empty():
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        with pytest.raises(InputValidationError, match="empty"):
            validate_input_file(f.name, "image/png")


def test_validate_input_file_valid():
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
        f.flush()
        validate_input_file(f.name, "image/png")  # should not raise
