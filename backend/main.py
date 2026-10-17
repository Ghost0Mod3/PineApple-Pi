from contextlib import asynccontextmanager
from datetime import datetime,timezone
from pathlib import Path
import glob,os,re,shutil,subprocess
from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .config import settings
from .database import connect,init_db

class Ack(BaseModel): accepted:bool
class Project(BaseModel): name:str;owner:str;scope:str;expires_at:str=''
class APSettings(BaseModel):
    ssid:str='PineApplePi-Toolkit';band:str='bg';channel:int=6
    open_network:bool=True;internet_sharing:bool=True;client_isolation:bool=True
    confirmation:str=''
class APAction(BaseModel): action:str
class ToolInstallRequest(BaseModel): tool_id:str;confirmation_token:str
TOOLS=[
 ('wireshark','Wireshark / TShark','tshark','apt package: tshark'),
 ('tcpdump','tcpdump','tcpdump','apt package: tcpdump'),('nmap','Nmap','nmap','apt package: nmap'),
 ('arpscan','arp-scan','arp-scan','apt package: arp-scan'),('lynis','Lynis','lynis','apt package: lynis'),
 ('reconng','Recon-ng','recon-ng','dedicated recipe required'),
 ('spiderfoot','SpiderFoot','spiderfoot','dedicated recipe required'),
 ('harvester','theHarvester','theHarvester','dedicated recipe required'),
 ('meshtastic','Meshtastic','meshtastic','pipx isolated application'),
 ('rtlsdr','RTL-SDR','rtl_test','apt package: rtl-sdr'),
 ('nodered','Node-RED','node-red','dedicated recipe required'),('docker','Docker','docker','apt package: docker.io')]
INSTALLABLE={'wireshark','tcpdump','nmap','arpscan','lynis','meshtastic','rtlsdr','docker'}

@asynccontextmanager
async def life(app): init_db();yield
app=FastAPI(docs_url=None,openapi_url=None,lifespan=life)
app.mount('/assets',StaticFiles(directory=settings.frontend/'assets'),name='assets')

def me(): return {'user_id':0,'username':'local-prototype','role':'administrator','enabled':True}
@app.get('/api/auth/status')
def status(): return {'setup_required':False,'authenticated':True,'user':me()}
@app.post('/api/acknowledgement')
def acknowledge(x:Ack,u=Depends(me)):
    if not x.accepted: raise HTTPException(400,'Acceptance required')
    with connect() as d:d.execute('INSERT INTO acknowledgements(accepted_at,version) VALUES(?,?)',(datetime.now(timezone.utc).isoformat(),'2026-10'))
    return {'ok':True}
@app.get('/api/tools')
def tools(u=Depends(me)):
    return {'items':[{'id':i,'name':n,'installed':bool(shutil.which(b)),'install':c,'supported':i in INSTALLABLE} for i,n,b,c in TOOLS]}

def nmcli(*args): return subprocess.run(['/usr/bin/nmcli',*args],capture_output=True,text=True,timeout=30)
def ap_status():
    r=nmcli('-t','-f','GENERAL.STATE,GENERAL.CONNECTION','device','show',settings.ap)
    return {'interface':settings.ap,'connected':'100 (connected)' in r.stdout,'details':r.stdout.strip()}
@app.get('/api/settings')
def cfg(u=Depends(me)):
    return {'host_interface':settings.host,'ap_interface':settings.ap,'inventory_interface':settings.inventory,'ap_ssid':'PineApplePi-Toolkit','ap_address':'10.42.0.1/24','band':'bg','channel':6,'allow_ap_changes':settings.enable_ap,'ap_status':ap_status()}
@app.post('/api/settings/ap/configure')
def configure_ap(x:APSettings,u=Depends(me)):
    if not settings.enable_ap: raise HTTPException(403,'AP changes disabled in .env')
    if settings.ap!='wlan2': raise HTTPException(400,'AP changes restricted to wlan2')
    if x.confirmation!='OPEN NETWORK' or not x.open_network: raise HTTPException(400,'Type OPEN NETWORK to confirm')
    if not 1<=len(x.ssid)<=32: raise HTTPException(400,'SSID must be 1-32 characters')
    allowed={'bg':{1,6,11},'a':{36,40,44,48}}
    if x.band not in allowed or x.channel not in allowed[x.band]: raise HTTPException(400,'Unsupported band or channel')
    subprocess.run(['/usr/bin/nmcli','connection','delete',settings.ap_connection],capture_output=True)
    cmds=[
      ['connection','add','type','wifi','ifname',settings.ap,'con-name',settings.ap_connection,'ssid',x.ssid],
      ['connection','modify',settings.ap_connection,'802-11-wireless.mode','ap','802-11-wireless.band',x.band,'802-11-wireless.channel',str(x.channel),'802-11-wireless-security.key-mgmt','none','802-11-wireless.ap-isolation','yes' if x.client_isolation else 'no','ipv4.method','shared','ipv4.addresses','10.42.0.1/24','ipv4.never-default','yes','ipv6.method','disabled','connection.autoconnect','no']]
    for c in cmds:
      r=nmcli(*c)
      if r.returncode: raise HTTPException(500,r.stderr.strip() or 'nmcli failed')
    return {'ok':True,'channel':x.channel}
@app.post('/api/settings/ap/action')
def control_ap(x:APAction,u=Depends(me)):
    if not settings.enable_ap: raise HTTPException(403,'AP changes disabled in .env')
    if x.action not in {'start','stop'}: raise HTTPException(400,'Invalid action')
    r=nmcli('connection','up' if x.action=='start' else 'down',settings.ap_connection)
    if r.returncode: raise HTTPException(500,r.stderr.strip() or 'nmcli failed')
    return {'ok':True,'status':ap_status()}

def leases():
    out={}
    for f in glob.glob('/var/lib/NetworkManager/*lease*')+glob.glob('/var/lib/misc/dnsmasq.leases'):
      try:
       for line in Path(f).read_text(errors='ignore').splitlines():
        p=line.split()
        if len(p)>=4 and re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}',p[1].lower()):out[p[1].lower()]={'ip':p[2],'hostname':p[3] if p[3]!='*' else ''}
      except OSError: pass
    return out

def parse_clients():
    now=datetime.now(timezone.utc).isoformat(); found={}; ls=leases()
    r=subprocess.run(['/usr/sbin/ip','-4','neigh','show','dev',settings.ap],capture_output=True,text=True)
    for line in r.stdout.splitlines():
      p=line.split();
      if 'lladdr' not in p: continue
      ip=p[0];mac=p[p.index('lladdr')+1].lower();state=p[-1];found[mac]={'ip':ip,'mac':mac,'hostname':ls.get(mac,{}).get('hostname',''),'state':state,'online':state not in {'FAILED','INCOMPLETE'}}
    with connect() as d:
      known={r['mac']:dict(r) for r in d.execute('SELECT * FROM ap_clients')}
      for mac,c in found.items():
       first=known.get(mac,{}).get('first_seen',now)
       d.execute('INSERT INTO ap_clients(mac,ip,hostname,first_seen,last_seen,online,state) VALUES(?,?,?,?,?,?,?) ON CONFLICT(mac) DO UPDATE SET ip=excluded.ip,hostname=excluded.hostname,last_seen=excluded.last_seen,online=1,state=excluded.state',(mac,c['ip'],c['hostname'],first,now,1,c['state']))
       if mac not in known or not known[mac]['online']:d.execute('INSERT INTO ap_events(mac,ip,hostname,event,created_at) VALUES(?,?,?,?,?)',(mac,c['ip'],c['hostname'],'connected',now))
      for mac,o in known.items():
       if o['online'] and mac not in found:
        d.execute('UPDATE ap_clients SET online=0,last_seen=? WHERE mac=?',(now,mac));d.execute('INSERT INTO ap_events(mac,ip,hostname,event,created_at) VALUES(?,?,?,?,?)',(mac,o['ip'],o['hostname'],'disconnected',now))
      clients=[dict(x) for x in d.execute('SELECT * FROM ap_clients ORDER BY online DESC,last_seen DESC')]
      events=[dict(x) for x in d.execute('SELECT * FROM ap_events ORDER BY id DESC LIMIT 100')]
    return {'clients':clients,'events':events,'online':sum(x['online'] for x in clients),'total':len(clients)}
@app.get('/api/settings/ap/activity')
def activity(u=Depends(me)): return parse_clients()
@app.delete('/api/settings/ap/activity')
def clear_activity(u=Depends(me)):
    with connect() as d:d.execute('DELETE FROM ap_events');d.execute('DELETE FROM ap_clients')
    return {'ok':True}
@app.get('/api/projects')
def projects(u=Depends(me)):
    with connect() as d:return {'items':[dict(x) for x in d.execute('SELECT * FROM projects ORDER BY id DESC')]}
@app.post('/api/projects')
def add_project(x:Project,u=Depends(me)):
    with connect() as d:d.execute('INSERT INTO projects(name,owner,scope,expires_at,state,created_at) VALUES(?,?,?,?,?,?)',(x.name,x.owner,x.scope,x.expires_at,'ACTIVE',datetime.now(timezone.utc).isoformat()))
    return {'ok':True}
@app.get('/api/install/status')
def install_status(u=Depends(me)):
    return {'helper_ready':os.path.isfile('/usr/local/sbin/pineapple-tool-installer'),'supported':sorted(INSTALLABLE),'token_command':'sudo pineapple-tool-installer issue-token'}
@app.post('/api/install/tool')
def install_tool(x:ToolInstallRequest,u=Depends(me)):
    tool=x.tool_id.strip().lower();token=x.confirmation_token.strip()
    if tool not in INSTALLABLE: raise HTTPException(400,'Dedicated reviewed installer required')
    if not token or len(token)>64: raise HTTPException(400,'Local confirmation token required')
    try:r=subprocess.run(['/usr/bin/sudo','-n','/usr/local/sbin/pineapple-tool-installer','install',tool,token],capture_output=True,text=True,timeout=900)
    except subprocess.TimeoutExpired: raise HTTPException(504,'Installation timed out')
    output=(r.stdout+'\n'+r.stderr).strip()[-12000:]
    if r.returncode: raise HTTPException(500,output or 'Installation failed')
    return {'ok':True,'output':output,'tool_id':tool}
@app.get('/healthz')
def health():return {'status':'ok','version':settings.version}
@app.get('/favicon.ico',include_in_schema=False)
def favicon():return FileResponse(settings.frontend/'assets/login-logo.jpg')
@app.get('/{path:path}',include_in_schema=False)
def spa(path=''):return FileResponse(settings.frontend/'index.html')
