"""
Guardrails for AI input/output validation.

Responsibilities:
- Validate input files before sending to the model (type, size, content)
- Validate and sanitize model output (schema, field lengths, allowed values)
- Detect cases where the model returned an error or off-topic response
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
ALLOWED_FILE_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/webp", "image/gif", "application/pdf"}
)
ALLOWED_COMPONENT_TYPES = frozenset(
    {
        "service", "database", "queue", "gateway", "cache",
        "load_balancer", "external", "cdn", "storage", "auth",
        "monitoring", "other",
    }
)
ALLOWED_SEVERITY = frozenset({"high", "medium", "low"})
MAX_FIELD_LENGTH = 400


class InputValidationError(ValueError):
    pass


class OutputValidationError(ValueError):
    pass


def validate_input_file(file_path: str, file_type: str) -> None:
    path = Path(file_path)
    if not path.exists():
        raise InputValidationError(f"File not found: {file_path}")
    if file_type not in ALLOWED_FILE_TYPES:
        raise InputValidationError(f"Disallowed file type: {file_type}")
    size = path.stat().st_size
    if size == 0:
        raise InputValidationError("File is empty")
    if size > MAX_FILE_SIZE_BYTES:
        raise InputValidationError(f"File too large: {size} bytes (max {MAX_FILE_SIZE_BYTES})")


def _truncate(value: str, max_len: int = MAX_FIELD_LENGTH) -> str:
    return value[:max_len] if isinstance(value, str) else value


def validate_and_sanitize_output(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    if not raw_text:
        raise OutputValidationError("Empty response from AI model")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise OutputValidationError(f"AI response is not valid JSON: {e}") from e

    if not isinstance(data, dict):
        raise OutputValidationError("AI response is not a JSON object")

    if "error" in data:
        raise OutputValidationError(f"Model returned error: {data['error']}")

    # Required top-level fields
    for field in ("summary", "components", "architectural_risks", "recommendations"):
        if field not in data:
            raise OutputValidationError(f"Missing required field: '{field}'")

    data["summary"] = _truncate(str(data["summary"]))

    if not isinstance(data["components"], list) or len(data["components"]) == 0:
        raise OutputValidationError("'components' must be a non-empty list")

    sanitized_components = []
    for c in data["components"]:
        if not isinstance(c, dict):
            continue
        comp_type = str(c.get("type", "other")).lower()
        if comp_type not in ALLOWED_COMPONENT_TYPES:
            comp_type = "other"
        sanitized_components.append(
            {
                "name": _truncate(str(c.get("name", "Unknown"))),
                "type": comp_type,
                "description": _truncate(str(c.get("description", ""))),
            }
        )
    data["components"] = sanitized_components

    sanitized_risks = []
    for r in data.get("architectural_risks", []):
        if not isinstance(r, dict):
            continue
        severity = str(r.get("severity", "medium")).lower()
        if severity not in ALLOWED_SEVERITY:
            severity = "medium"
        sanitized_risks.append(
            {
                "severity": severity,
                "title": _truncate(str(r.get("title", ""))),
                "description": _truncate(str(r.get("description", ""))),
            }
        )
    data["architectural_risks"] = sanitized_risks

    sanitized_recs = []
    for rec in data.get("recommendations", []):
        if not isinstance(rec, dict):
            continue
        priority = str(rec.get("priority", "medium")).lower()
        if priority not in ALLOWED_SEVERITY:
            priority = "medium"
        sanitized_recs.append(
            {
                "priority": priority,
                "title": _truncate(str(rec.get("title", ""))),
                "action": _truncate(str(rec.get("action", ""))),
            }
        )
    data["recommendations"] = sanitized_recs

    logger.info(
        "Output validated: %d components, %d risks, %d recommendations",
        len(data["components"]),
        len(data["architectural_risks"]),
        len(data["recommendations"]),
    )
    return data
