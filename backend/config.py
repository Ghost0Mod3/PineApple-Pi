from pathlib import Path
import os
from dotenv import load_dotenv
BASE=Path(__file__).resolve().parent.parent;load_dotenv(BASE/'.env')
class S:
 version=os.getenv('APP_VERSION','0.6.4-ap-clean');cookie=os.getenv('SESSION_COOKIE_NAME','pineapple_session')
 db=BASE/os.getenv('DATABASE_PATH','database/pineapple_pi.db');frontend=BASE/os.getenv('FRONTEND_PATH','frontend')
 host=os.getenv('HOST_INTERFACE','wlan1');ap=os.getenv('ACCESS_POINT_INTERFACE','wlan2');inventory=os.getenv('INVENTORY_INTERFACE','wlan0')
 enable_ap=os.getenv('ENABLE_AP_CHANGES','false').lower()=='true';ap_connection=os.getenv('AP_CONNECTION_NAME','PineApple-AP')
settings=S()
