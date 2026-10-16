from dataclasses import dataclass
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,subprocess,uuid,ipaddress
from backend.config import settings
from backend.database import connect
from backend.security import iso
ARTIFACTS=settings.db.parent.parent/'data/artifacts';ARTIFACTS.mkdir(parents=True,exist_ok=True)
@dataclass(frozen=True)
class Tool:id:str;name:str;group:str;binary:str;gate:str;mode:str;description:str;enabled:bool
TOOLS={
'wireshark':Tool('wireshark','Wireshark / TShark','Network Analysis','tshark','authorization','capture','Bounded packet capture and protocol summaries',False),
'tcpdump':Tool('tcpdump','tcpdump','Network Analysis','tcpdump','authorization','capture','Limited troubleshooting packet capture',False),
'nmap':Tool('nmap','Nmap','Network Analysis','nmap','authorization','network','Approved private host and service inventory',True),
'arpscan':Tool('arpscan','arp-scan','Network Analysis','arp-scan','authorization','network','Directly attached IPv4 discovery on wlan3',True),
'lynis':Tool('lynis','Lynis','System Security','lynis','admin','local','Local PineApple-Pi hardening audit',True),
'reconng':Tool('reconng','Recon-ng','Authorized OSINT','recon-ng','authorization','passive','Authorized public-source workspace',False),
'spiderfoot':Tool('spiderfoot','SpiderFoot','Authorized OSINT','docker','authorization','container','Passive OSINT container workflow',False),
'harvester':Tool('harvester','theHarvester','Authorized OSINT','docker','authorization','container','Passive domain and certificate discovery',False),
'meshtastic':Tool('meshtastic','Meshtastic','Radio & Mesh','meshtastic','admin','read-only','Read-only mesh status and telemetry',True),
'rtlsdr':Tool('rtlsdr','RTL-SDR','Radio & Mesh','rtl_test','authorization','receive-only','Receive-only hardware test',True),
'nodered':Tool('nodered','Node-RED','Automation & Services','node-red','admin','service','Visual approved-event automation',False),
'docker':Tool('docker','Docker','Automation & Services','docker','admin','service','Restricted approved service lifecycle',True)}
def health():
 return [{'id':t.id,'name':t.name,'group':t.group,'installed':bool(shutil.which(t.binary)),'path':shutil.which(t.binary),'gate':t.gate,'mode':t.mode,'description':t.description,'execution_enabled':t.enabled} for t in TOOLS.values()]
def authorized(session_id,tool,target):
 if tool.gate!='authorization':return True
 with connect() as d:r=d.execute("SELECT * FROM authorization_sessions WHERE id=? AND state='ACTIVE'",(session_id or '',)).fetchone()
 if not r or datetime.fromisoformat(r['expires_at'])<=datetime.now(timezone.utc):return False
 if tool.id not in json.loads(r['tools_json']):return False
 targets=json.loads(r['targets_json'])
 if target in targets:return True
 try:
  ip=ipaddress.ip_address(target)
  return any('/' in x and ip in ipaddress.ip_network(x,strict=False) for x in targets)
 except ValueError:return False
def command(tool,cfg,folder):
 if tool.id=='nmap':
  target=cfg.get('Authorized target','');net=ipaddress.ip_network(target,strict=False)
  if not net.is_private or net.prefixlen<24:raise ValueError('Target must be a private /24 or smaller network')
  profiles={'Host discovery':['-sn'],'Common services':['-sT','--top-ports','100'],'Approved device review':['-sT','-sV','--top-ports','100'],'Gateway review':['-sT','--top-ports','50']}
  return ['nmap',*profiles[cfg.get('Scan profile','Host discovery')],'-oX',str(folder/'nmap.xml'),target]
 if tool.id=='arpscan':return ['arp-scan','--interface='+settings.assessment,'--localnet']
 if tool.id=='lynis':return ['lynis','audit','system','--quick','--no-colors']
 if tool.id=='meshtastic':return ['meshtastic','--info']
 if tool.id=='rtlsdr':return ['rtl_test','-t']
 if tool.id=='docker':
  action=cfg.get('Action','View logs');service=cfg.get('Approved service','SpiderFoot').lower().replace(' ','-')
  if action=='View logs':return ['docker','compose','logs','--tail','100',service]
  if action in {'Start','Stop','Restart'}:return ['docker','compose',action.lower(),service]
 raise ValueError('Execution adapter is disabled in this release candidate')
def run(tool_id,cfg,uid,session_id=None):
 tool=TOOLS.get(tool_id)
 if not tool:raise ValueError('Unknown tool')
 if not tool.enabled:raise ValueError('GUI is wired, but this execution adapter remains disabled in rc1')
 if not shutil.which(tool.binary):raise ValueError(f'{tool.name} is not installed')
 target=cfg.get('Authorized target') or cfg.get('Authorized domain') or cfg.get('Authorized public target') or 'local'
 if not authorized(session_id,tool,target):raise ValueError('Active authorization does not permit this tool and target')
 jid=str(uuid.uuid4());folder=ARTIFACTS/jid;folder.mkdir(parents=True)
 cmd=command(tool,cfg,folder);started=iso()
 with connect() as d:d.execute('INSERT INTO tool_jobs(id,tool_id,user_id,state,created_at,config_json,artifact_dir) VALUES(?,?,?,?,?,?,?)',(jid,tool_id,uid,'RUNNING',started,json.dumps(cfg),str(folder)))
 try:proc=subprocess.run(cmd,text=True,capture_output=True,timeout=300,check=False)
 except subprocess.TimeoutExpired:raise ValueError('Job reached its five-minute limit')
 (folder/'stdout.txt').write_text(proc.stdout or '');(folder/'stderr.txt').write_text(proc.stderr or '')
 summary=(proc.stdout or proc.stderr or 'No output')[:5000]
 with connect() as d:d.execute('UPDATE tool_jobs SET state=?,finished_at=?,return_code=?,summary=? WHERE id=?',('COMPLETED',iso(),proc.returncode,summary,jid))
 return {'job_id':jid,'tool_id':tool_id,'return_code':proc.returncode,'summary':summary,'artifact_dir':str(folder)}
