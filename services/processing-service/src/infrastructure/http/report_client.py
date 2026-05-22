import logging

import httpx

from ...config import settings

logger = logging.getLogger(__name__)


class ReportServiceClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._client = http_client
        self._base_url = settings.report_service_url

    async def save_report(self, analysis_id: str, report_data: dict) -> None:
        payload = {"analysis_id": analysis_id, **report_data}
        try:
            response = await self._client.post(
                f"{self._base_url}/reports",
                json=payload,
                timeout=15.0,
            )
            response.raise_for_status()
            logger.info("Report saved for analysis %s", analysis_id)
        except httpx.HTTPError as e:
            logger.error("Failed to save report for %s: %s", analysis_id, e)
            raise
