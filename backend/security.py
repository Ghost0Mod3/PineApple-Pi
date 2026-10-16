from datetime import datetime,timedelta,timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import hashlib,secrets
from backend.database import connect
PH=PasswordHasher()
def now():return datetime.now(timezone.utc)
def iso(x=None):return (x or now()).isoformat()
def h(x):return hashlib.sha256(x.encode()).hexdigest()
def setup_required():
 with connect() as d:return d.execute('SELECT 1 FROM users').fetchone() is None
def create_admin(u,p):
 if not setup_required():raise ValueError('Setup already completed')
 if len(p)<12:raise ValueError('Password must be at least 12 characters')
 with connect() as d:return d.execute('INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)',(u.strip(),PH.hash(p),iso())).lastrowid
def verify(u,p):
 with connect() as d:r=d.execute('SELECT * FROM users WHERE username=?',(u.strip(),)).fetchone()
 if not r:return None
 try:PH.verify(r['password_hash'],p);return dict(r)
 except VerifyMismatchError:return None
def new_session(uid):
 t=secrets.token_urlsafe(32);n=now()
 with connect() as d:d.execute('INSERT INTO sessions VALUES(?,?,?,?,0)',(h(t),uid,iso(n),iso(n+timedelta(hours=8))))
 return t
def get_session(t):
 if not t:return None
 with connect() as d:r=d.execute('SELECT s.*,u.username,u.role FROM sessions s JOIN users u ON u.id=s.user_id WHERE token_hash=? AND revoked=0',(h(t),)).fetchone()
 if not r or datetime.fromisoformat(r['expires_at'])<=now():return None
 return dict(r)
def revoke(t):
 if t:
  with connect() as d:d.execute('UPDATE sessions SET revoked=1 WHERE token_hash=?',(h(t),))
