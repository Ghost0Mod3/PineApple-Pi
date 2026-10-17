from contextlib import asynccontextmanager
from fastapi import FastAPI,Cookie,Depends,HTTPException,Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from backend.config import settings
from backend.database import init_db,connect
from backend import security
from datetime import datetime,timezone
import shutil,subprocess,re,glob,json
class Cred(BaseModel):username:str;password:str=Field(min_length=12)
class Ack(BaseModel):accepted:bool
class Project(BaseModel):name:str;owner:str;scope:str;expires_at:str
class APSettings(BaseModel):
 ssid:str=Field(min_length=1,max_length=32)
 band:str='a'
 channel:int=36
 open_network:bool=False
 internet_sharing:bool=True
 client_isolation:bool=True
 confirmation:str=''
class APAction(BaseModel):action:str
TOOLS=[('wireshark','Wireshark / TShark','tshark','apt install tshark'),('tcpdump','tcpdump','tcpdump','apt install tcpdump'),('nmap','Nmap','nmap','apt install nmap'),('arpscan','arp-scan','arp-scan','apt install arp-scan'),('lynis','Lynis','lynis','apt install lynis'),('reconng','Recon-ng','recon-ng','review upstream install'),('spiderfoot','SpiderFoot','docker','review official container'),('harvester','theHarvester','theHarvester','review upstream install'),('meshtastic','Meshtastic','meshtastic','pipx install meshtastic[cli]'),('rtlsdr','RTL-SDR','rtl_test','apt install rtl-sdr'),('nodered','Node-RED','node-red','review official install'),('docker','Docker','docker','apt install docker.io')]
@asynccontextmanager
async def life(app):init_db();yield
app=FastAPI(docs_url=None,openapi_url=None,lifespan=life)
def me(pineapple_session:str|None=Cookie(None,alias=settings.cookie)):
 u=security.get(pineapple_session)
 if not u:raise HTTPException(401,'Authentication required')
 return u
@app.get('/api/auth/status')
def status(pineapple_session:str|None=Cookie(None,alias=settings.cookie)):return {'setup_required':security.setup_required(),'authenticated':bool(security.get(pineapple_session))}
@app.post('/api/auth/setup')
def setup(x:Cred,r:Response):
 try:uid=security.create(x.username,x.password)
 except ValueError as e:raise HTTPException(400,str(e))
 r.set_cookie(settings.cookie,security.session(uid),httponly=True,samesite='strict');return {'ok':True}
@app.post('/api/auth/login')
def login(x:Cred,r:Response):
 u=security.verify(x.username,x.password)
 if not u:raise HTTPException(401,'Invalid credentials')
 r.set_cookie(settings.cookie,security.session(u['id']),httponly=True,samesite='strict');return {'ok':True}
@app.post('/api/auth/logout')
def logout(r:Response):r.delete_cookie(settings.cookie);return {'ok':True}
@app.post('/api/acknowledgement')
def acknowledge(x:Ack,u=Depends(me)):
 if not x.accepted:raise HTTPException(400,'Acceptance required')
 with connect() as d:d.execute('INSERT INTO acknowledgements(user_id,accepted_at,version) VALUES(?,?,?)',(u['user_id'],datetime.now(timezone.utc).isoformat(),'2026-10'))
 return {'ok':True}
@app.get('/api/tools')
def tools(u=Depends(me)):return {'items':[{'id':i,'name':n,'installed':bool(shutil.which(b)),'install':c,'color':'yellow'} for i,n,b,c in TOOLS]}
def nmcli(*args):
 p=subprocess.run(['nmcli',*args],text=True,capture_output=True,timeout=30,check=False)
 if p.returncode:raise HTTPException(400,(p.stderr or p.stdout or 'nmcli failed').strip())
 return p.stdout.strip()
def ap_status():
 if not shutil.which('nmcli'):return {'available':False,'active':False,'state':'NetworkManager CLI unavailable'}
 p=subprocess.run(['nmcli','-t','-f','GENERAL.STATE,GENERAL.CONNECTION','device','show',settings.ap],text=True,capture_output=True,timeout=10)
 text=p.stdout;return {'available':True,'active':settings.ap_connection in text,'state':text.strip() or 'unknown'}
@app.get('/api/settings')
def cfg(u=Depends(me)):return {'host_interface':settings.host,'ap_interface':settings.ap,'inventory_interface':settings.inventory,'ap_ssid':'PineApplePi-Toolkit','ap_address':'10.42.0.1/24','prototype':True,'allow_ap_changes':settings.enable_ap,'ap_status':ap_status()}
@app.post('/api/settings/ap/configure')
def configure_ap(x:APSettings,u=Depends(me)):
 if not settings.enable_ap:raise HTTPException(403,'AP changes are disabled. Set ENABLE_AP_CHANGES=true after prototype validation.')
 if settings.ap!='wlan2':raise HTTPException(400,'Open-AP controls are locked to wlan2')
 if not re.fullmatch(r'[ -~]{1,32}',x.ssid):raise HTTPException(400,'SSID contains unsupported characters')
 if x.band not in {'a','bg'}:raise HTTPException(400,'Band must be a or bg')
 allowed={36,40,44,48} if x.band=='a' else {1,6,11}
 if x.channel not in allowed:raise HTTPException(400,'Channel is not in the approved prototype set')
 if not x.open_network or x.confirmation!='OPEN NETWORK':raise HTTPException(400,'Open AP requires the confirmation phrase OPEN NETWORK')
 subprocess.run(['nmcli','connection','delete',settings.ap_connection],text=True,capture_output=True,timeout=15)
 nmcli('connection','add','type','wifi','ifname',settings.ap,'con-name',settings.ap_connection,'ssid',x.ssid)
 nmcli('connection','modify',settings.ap_connection,'connection.interface-name',settings.ap,'connection.autoconnect','yes','802-11-wireless.mode','ap','802-11-wireless.band',x.band,'802-11-wireless.channel',str(x.channel),'802-11-wireless.hidden','no','802-11-wireless.ap-isolation','yes' if x.client_isolation else 'no','802-11-wireless-security.key-mgmt','none','ipv4.method','shared' if x.internet_sharing else 'manual','ipv4.addresses','10.42.0.1/24','ipv4.never-default','yes','ipv6.method','disabled')
 return {'ok':True,'message':'Open AP profile configured','status':ap_status()}
@app.post('/api/settings/ap/action')
def control_ap(x:APAction,u=Depends(me)):
 if not settings.enable_ap:raise HTTPException(403,'AP changes are disabled')
 if x.action=='start':nmcli('connection','up',settings.ap_connection)
 elif x.action=='stop':nmcli('connection','down',settings.ap_connection)
 else:raise HTTPException(400,'Action must be start or stop')
 return {'ok':True,'status':ap_status()}

def parse_ap_neighbours():
 now=datetime.now(timezone.utc).isoformat();found={}
 if shutil.which('ip'):
  result=subprocess.run(['ip','-4','neigh','show','dev',settings.ap],text=True,capture_output=True,timeout=10)
  for line in result.stdout.splitlines():
   parts=line.split()
   if not parts:continue
   ip=parts[0];state=parts[-1];mac=''
   if 'lladdr' in parts:
    idx=parts.index('lladdr');mac=parts[idx+1].lower() if idx+1<len(parts) else ''
   if mac and state not in {'FAILED','INCOMPLETE'}:found[mac]={'ip':ip,'hostname':'','state':state,'source':'neighbour'}
 for lease in glob.glob('/var/lib/NetworkManager/dnsmasq-*.leases')+glob.glob('/var/lib/misc/dnsmasq.leases'):
  try:
   for line in open(lease,errors='ignore'):
    parts=line.split()
    if len(parts)>=4:
     _,mac,ip,host=parts[:4];mac=mac.lower();item=found.setdefault(mac,{'ip':ip,'hostname':'','state':'LEASED','source':'dhcp'})
     item['ip']=ip;item['hostname']='' if host=='*' else host;item['source']='dhcp+neighbour' if item['source']=='neighbour' else 'dhcp'
  except OSError:pass
 with connect() as d:
  previous={r['mac']:dict(r) for r in d.execute('SELECT * FROM ap_clients')}
  sql="INSERT INTO ap_clients(mac,ip,hostname,interface,first_seen,last_seen,state,source) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(mac) DO UPDATE SET ip=excluded.ip,hostname=CASE WHEN excluded.hostname!='' THEN excluded.hostname ELSE ap_clients.hostname END,last_seen=excluded.last_seen,state=excluded.state,source=excluded.source"
  for mac,item in found.items():
   if mac not in previous:d.execute('INSERT INTO ap_activity(created_at,event,mac,ip,hostname,details) VALUES(?,?,?,?,?,?)',(now,'connected',mac,item['ip'],item['hostname'],json.dumps({'interface':settings.ap})))
   d.execute(sql,(mac,item['ip'],item['hostname'],settings.ap,previous.get(mac,{}).get('first_seen',now),now,item['state'],item['source']))
  for mac,item in previous.items():
   if mac not in found and item['state']!='OFFLINE':
    d.execute('UPDATE ap_clients SET state=?,last_seen=? WHERE mac=?',('OFFLINE',now,mac));d.execute('INSERT INTO ap_activity(created_at,event,mac,ip,hostname,details) VALUES(?,?,?,?,?,?)',(now,'disconnected',mac,item['ip'],item['hostname'],'{}'))
  clients=[dict(r) for r in d.execute("SELECT * FROM ap_clients ORDER BY CASE WHEN state='OFFLINE' THEN 1 ELSE 0 END,last_seen DESC")]
  activity=[dict(r) for r in d.execute('SELECT * FROM ap_activity ORDER BY id DESC LIMIT 100')]
 return {'interface':settings.ap,'clients':clients,'activity':activity,'refreshed_at':now}

@app.get('/api/settings/ap/activity')
def get_ap_activity(u=Depends(me)):return parse_ap_neighbours()
@app.delete('/api/settings/ap/activity')
def clear_ap_activity(u=Depends(me)):
 with connect() as d:d.execute('DELETE FROM ap_activity');d.execute('DELETE FROM ap_clients')
 return {'ok':True}

@app.get('/api/projects')
def projects(u=Depends(me)):
 with connect() as d:return {'items':[dict(x) for x in d.execute('SELECT * FROM authorization_projects ORDER BY id DESC')]}
@app.post('/api/projects')
def add_project(x:Project,u=Depends(me)):
 with connect() as d:i=d.execute('INSERT INTO authorization_projects(name,owner,scope,expires_at) VALUES(?,?,?,?)',(x.name,x.owner,x.scope,x.expires_at)).lastrowid
 return {'id':i}
@app.get('/healthz')
def hz():return {'status':'ok','version':settings.version}
app.mount('/assets',StaticFiles(directory=settings.frontend/'assets'),name='assets')
@app.get('/{path:path}',include_in_schema=False)
def spa(path=''):return FileResponse(settings.frontend/'index.html')
