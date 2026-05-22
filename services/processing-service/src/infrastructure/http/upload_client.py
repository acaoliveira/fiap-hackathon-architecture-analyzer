import logging

import httpx

from ...config import settings

logger = logging.getLogger(__name__)


class UploadServiceClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._client = http_client
        self._base_url = settings.upload_service_url

    async def set_status(self, analysis_id: str, status: str, error_message: str | None = None) -> None:
        payload: dict = {"status": status}
        if error_message:
            payload["error_message"] = error_message[:500]
        try:
            response = await self._client.patch(
                f"{self._base_url}/analyses/{analysis_id}/status",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info("Updated analysis %s status → %s", analysis_id, status)
        except httpx.HTTPError as e:
            logger.error("Failed to update status for %s: %s", analysis_id, e)
