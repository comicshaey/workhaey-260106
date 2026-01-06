from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    APP_NAME: str = "eduworkhaey 업무보조 포털"
    TMP_DIR: Path = Path("storage/tmp")
    MAX_UPLOAD_MB: int = 25  # 파일당 대충 안전선

settings = Settings()
