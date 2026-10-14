import os, platform, time
import psutil

def temperature():
    try:
        for entries in psutil.sensors_temperatures().values():
            if entries: return entries[0].current
    except (AttributeError,OSError): pass
    return None

def get_system_health(): return {'hostname':platform.node(),'platform':platform.platform(),'cpu_percent':psutil.cpu_percent(interval=.1),'memory_percent':psutil.virtual_memory().percent,'disk_percent':psutil.disk_usage('/').percent,'temperature_c':temperature(),'uptime_seconds':int(time.time()-psutil.boot_time()),'load_average':list(os.getloadavg()) if hasattr(os,'getloadavg') else None}
