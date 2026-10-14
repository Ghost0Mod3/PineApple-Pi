from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def project_path(name: str, default: Path) -> Path:
    value = Path(os.getenv(name, str(default)))
    return value if value.is_absolute() else BASE_DIR / value

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Pineapple-Pi")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    database_path: Path = project_path("DATABASE_PATH", BASE_DIR / "database" / "pineapple_pi.db")
    frontend_path: Path = project_path("FRONTEND_PATH", BASE_DIR / "frontend")
    management_interface: str = os.getenv("MANAGEMENT_INTERFACE", "wlan0")
    scanner_interface: str = os.getenv("SCANNER_INTERFACE", "wlan1")
    scanner_expected_mac: str = os.getenv("SCANNER_EXPECTED_MAC", "80:af:ca:eb:92:07").lower()
    scanner_expected_driver: str = os.getenv("SCANNER_EXPECTED_DRIVER", "rtw88_8822bu")
    scan_interval_seconds: int = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))
    allow_active_radio_changes: bool = os.getenv("ALLOW_ACTIVE_RADIO_CHANGES", "false").lower() == "true"

settings = Settings()
