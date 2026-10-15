from backend.config import settings
from backend.services.commands import run
from backend.services.radio_manager import get_radio_statuses

def run_preflight():
    radios=get_radio_statuses(); management=next(x for x in radios if x['role']=='management'); scanner=next(x for x in radios if x['role']=='inventory-scanner')
    route=run(['ip','route','show','default']).stdout.strip()
    connect=run(['rpi-connect','status'])
    checks={'management_present':management['state']!='missing','management_has_ip':bool(management['ip_address']),'default_route_on_management':f"dev {settings.management_interface}" in route,'scanner_identity_ok':scanner['identity_ok'],'scanner_not_management':settings.scanner_interface!=settings.management_interface,'active_changes_disabled':not settings.allow_active_radio_changes,'rpi_connect_command_ok':connect.returncode==0}
    return {'ok':all(checks.values()),'checks':checks,'radios':radios,'default_route':route,'rpi_connect_status':connect.stdout.strip() or connect.stderr.strip()}
