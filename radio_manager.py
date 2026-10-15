import json
from pathlib import Path
from backend.config import settings
from backend.services.commands import run

def _driver(iface:str):
    try: return ((Path('/sys/class/net')/iface/'device'/'driver').resolve().name)
    except OSError: return None

def _mac(iface:str):
    p=Path('/sys/class/net')/iface/'address'
    return p.read_text().strip().lower() if p.exists() else None

def _ip(iface:str):
    result=run(['ip','-j','addr','show','dev',iface])
    try:
        for item in json.loads(result.stdout or '[]')[0].get('addr_info',[]):
            if item.get('family')=='inet': return item.get('local')
    except (json.JSONDecodeError,IndexError): pass
    return None

def _nm_state(iface:str):
    result=run(['nmcli','-t','-f','GENERAL.STATE,GENERAL.CONNECTION','device','show',iface])
    values={}
    for line in result.stdout.splitlines():
        key,_,value=line.partition(':'); values[key]=value
    return values

def get_radio_statuses():
    items=[]
    for iface,role in ((settings.management_interface,'management'),(settings.scanner_interface,'inventory-scanner')):
        exists=(Path('/sys/class/net')/iface).exists(); nm=_nm_state(iface) if exists else {}
        mac=_mac(iface) if exists else None; driver=_driver(iface) if exists else None
        identity_ok=True
        if role=='inventory-scanner': identity_ok=(mac==settings.scanner_expected_mac and driver==settings.scanner_expected_driver)
        items.append({'interface':iface,'role':role,'state':nm.get('GENERAL.STATE','missing' if not exists else 'unknown'),'connection':nm.get('GENERAL.CONNECTION'),'driver':driver,'mac_address':mac,'ip_address':_ip(iface) if exists else None,'identity_ok':identity_ok})
    return items
