from datetime import datetime,timedelta,timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from backend.database import connect
import hashlib,secrets
PH=PasswordHasher();now=lambda:datetime.now(timezone.utc);iso=lambda x=None:(x or now()).isoformat();h=lambda x:hashlib.sha256(x.encode()).hexdigest()
def setup_required():
 with connect() as d:return d.execute('SELECT 1 FROM users').fetchone() is None
def create(u,p):
 if not setup_required():raise ValueError('Setup already completed')
 if len(p)<12:raise ValueError('Password must be 12+ characters')
 with connect() as d:return d.execute('INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)',(u,PH.hash(p),iso())).lastrowid
def verify(u,p):
 with connect() as d:r=d.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
 if not r:return None
 try:PH.verify(r['password_hash'],p);return dict(r)
 except VerifyMismatchError:return None
def session(uid):
 t=secrets.token_urlsafe(32)
 with connect() as d:d.execute('INSERT INTO sessions VALUES(?,?,?,0)',(h(t),uid,iso(now()+timedelta(hours=8))))
 return t
def get(t):
 if not t:return None
 with connect() as d:r=d.execute('SELECT s.*,u.username FROM sessions s JOIN users u ON u.id=s.user_id WHERE token_hash=? AND revoked=0',(h(t),)).fetchone()
 return dict(r) if r and datetime.fromisoformat(r['expires_at'])>now() else None
