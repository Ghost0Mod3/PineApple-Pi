from datetime import datetime, timezone
import re
from backend.config import settings
from backend.database import db_connection
from backend.services.commands import run
from backend.services.preflight import run_preflight

BSSID_RE=re.compile(r'^[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}$')

def _split_nmcli(line:str):
    fields=[]; current=''; escaped=False
    for ch in line:
        if escaped: current+=ch; escaped=False
        elif ch=='\\': escaped=True
        elif ch==':': fields.append(current); current=''
        else: current+=ch
    fields.append(current); return fields

def parse_nmcli(text:str):
    items=[]
    for line in text.splitlines():
        fields=_split_nmcli(line)
        if len(fields)!=6: continue
        bssid,ssid,chan,freq,signal,security=fields
        if not BSSID_RE.match(bssid): continue
        def integer(value):
            try: return int(value)
            except ValueError: return None
        items.append({'bssid':bssid.lower(),'ssid':ssid or '<hidden>','channel':integer(chan),'frequency_mhz':integer(freq),'signal_percent':integer(signal),'security':security or 'OPEN/UNKNOWN'})
    return items

def scan_and_store():
    preflight=run_preflight()
    if not preflight['checks']['management_has_ip'] or not preflight['checks']['default_route_on_management']:
        raise RuntimeError('Management protection check failed; refusing scan')
    if not preflight['checks']['scanner_identity_ok']:
        raise RuntimeError('wlan1 hardware identity does not match approved adapter')
    result=run(['nmcli','--terse','--escape','yes','--fields','BSSID,SSID,CHAN,FREQ,SIGNAL,SECURITY','device','wifi','list','ifname',settings.scanner_interface,'--rescan','yes'],timeout=35)
    if result.returncode!=0: raise RuntimeError(result.stderr.strip() or 'NetworkManager scan failed')
    now=datetime.now(timezone.utc).isoformat(); items=parse_nmcli(result.stdout)
    with db_connection() as db:
        db.execute('INSERT INTO scan_runs(started_at,interface,result_count,status) VALUES(?,?,?,?)',(now,settings.scanner_interface,len(items),'ok'))
        for ap in items:
            db.execute("""INSERT INTO access_points(ssid,bssid,channel,frequency_mhz,signal_percent,security,first_seen,last_seen,sightings)
              VALUES(?,?,?,?,?,?,?,?,1)
              ON CONFLICT(bssid) DO UPDATE SET ssid=excluded.ssid,channel=excluded.channel,frequency_mhz=excluded.frequency_mhz,signal_percent=excluded.signal_percent,security=excluded.security,last_seen=excluded.last_seen,sightings=access_points.sightings+1""",(ap['ssid'],ap['bssid'],ap['channel'],ap['frequency_mhz'],ap['signal_percent'],ap['security'],now,now))
    return {'status':'ok','interface':settings.scanner_interface,'observed':len(items),'timestamp':now}
