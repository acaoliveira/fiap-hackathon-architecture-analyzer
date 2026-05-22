import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalStorage:
    def __init__(self, base_path: str) -> None:
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, analysis_id: str, file_name: str, content: bytes) -> str:
        dest_dir = self._base_path / analysis_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / file_name
        dest.write_bytes(content)
        logger.info("File saved: %s", dest)
        return str(dest)
