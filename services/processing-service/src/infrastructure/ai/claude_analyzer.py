import asyncio
import base64
import logging
from pathlib import Path

import anthropic

from ...config import settings
from .guardrails import InputValidationError, OutputValidationError, validate_and_sanitize_output, validate_input_file
from .prompts import ANALYSIS_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClaudeAnalyzer:
    """Calls the Claude API to analyze architecture diagrams.

    Supports both image files (PNG, JPEG, WEBP, GIF) and PDFs.
    Implements retry logic and guardrail validation on output.
    """

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _build_content_block(self, file_path: str, file_type: str) -> dict:
        data = base64.standard_b64encode(Path(file_path).read_bytes()).decode("utf-8")
        if file_type == "application/pdf":
            return {
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": data},
            }
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": file_type, "data": data},
        }

    async def analyze(self, file_path: str, file_type: str) -> dict:
        """Analyze a diagram and return a validated, sanitized report dict.

        Raises InputValidationError or OutputValidationError on failure.
        """
        validate_input_file(file_path, file_type)

        content_block = self._build_content_block(file_path, file_type)

        last_error: Exception | None = None
        for attempt in range(1, settings.max_retries + 1):
            try:
                logger.info("Claude API call — attempt %d/%d", attempt, settings.max_retries)
                response = await self._client.messages.create(
                    model=settings.claude_model,
                    max_tokens=settings.claude_max_tokens,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                content_block,
                                {"type": "text", "text": ANALYSIS_PROMPT},
                            ],
                        }
                    ],
                )
                raw_text = response.content[0].text
                return validate_and_sanitize_output(raw_text)

            except OutputValidationError:
                raise
            except InputValidationError:
                raise
            except anthropic.RateLimitError as e:
                logger.warning("Rate limit hit, backing off: %s", e)
                last_error = e
                await asyncio.sleep(2**attempt)
            except anthropic.APIError as e:
                logger.warning("API error on attempt %d: %s", attempt, e)
                last_error = e
                await asyncio.sleep(1)

        raise RuntimeError(f"Claude API failed after {settings.max_retries} attempts: {last_error}")
