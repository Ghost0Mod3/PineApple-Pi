from pathlib import Path
import os
from dotenv import load_dotenv
BASE=Path(__file__).resolve().parent.parent;load_dotenv(BASE/'.env')
class Settings:
 version=os.getenv('APP_VERSION','0.5.0-rc1')
 db=Path(os.getenv('DATABASE_PATH','database/pineapple_pi.db'));db=db if db.is_absolute() else BASE/db
 frontend=Path(os.getenv('FRONTEND_PATH','frontend'));frontend=frontend if frontend.is_absolute() else BASE/frontend
 management=os.getenv('MANAGEMENT_INTERFACE','wlan0');ap=os.getenv('ACCESS_POINT_INTERFACE','wlan2');assessment=os.getenv('ASSESSMENT_INTERFACE','wlan3')
 cookie=os.getenv('SESSION_COOKIE_NAME','pineapple_session')
settings=Settings()
