from pathlib import Path
import os
BASE=Path(__file__).resolve().parents[1]
class Settings:
    version=os.getenv('APP_VERSION','0.7.0-complete')
    database=(BASE/os.getenv('DATABASE_PATH','database/pineapple_pi.db')).resolve()
    frontend=(BASE/os.getenv('FRONTEND_PATH','frontend')).resolve()
    host=os.getenv('HOST_INTERFACE','wlan1')
    ap=os.getenv('ACCESS_POINT_INTERFACE','wlan2')
    inventory=os.getenv('INVENTORY_INTERFACE','wlan0')
    enable_ap=os.getenv('ENABLE_AP_CHANGES','false').lower()=='true'
    ap_connection=os.getenv('AP_CONNECTION_NAME','PineApple-AP')
settings=Settings()
