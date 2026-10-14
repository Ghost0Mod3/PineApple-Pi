from backend.database import db_connection

def list_access_points(limit=200):
    with db_connection() as db: return [dict(r) for r in db.execute('SELECT * FROM access_points ORDER BY last_seen DESC LIMIT ?',(limit,)).fetchall()]
def inventory_summary():
    with db_connection() as db:
        total=db.execute('SELECT COUNT(*) FROM access_points').fetchone()[0]
        bands=db.execute("SELECT CASE WHEN frequency_mhz < 3000 THEN '2.4 GHz' ELSE '5 GHz' END band, COUNT(*) count FROM access_points GROUP BY band").fetchall()
        last=db.execute('SELECT started_at,result_count,status FROM scan_runs ORDER BY id DESC LIMIT 1').fetchone()
    return {'total_access_points':total,'bands':{r['band']:r['count'] for r in bands},'last_scan':dict(last) if last else None}
