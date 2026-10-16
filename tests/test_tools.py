from backend.tools import TOOLS,health
def test_all_apps_registered():assert len(TOOLS)==12
def test_health_shape():assert all('installed' in x and 'execution_enabled' in x for x in health())
