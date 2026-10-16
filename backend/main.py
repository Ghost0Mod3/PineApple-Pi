from contextlib import asynccontextmanager
from fastapi import FastAPI,Cookie,Depends,HTTPException,Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from backend.config import settings
from backend.database import init_db,connect
from backend import security,tools
from backend.security import iso
import json,hashlib,secrets
class Cred(BaseModel):username:str;password:str=Field(min_length=12)
class Job(BaseModel):tool_id:str;config:dict;session_id:str|None=None
class Authz(BaseModel):tools:list[str];targets:list[str];expires_at:str
@asynccontextmanager
async def life(app):init_db();yield
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None,lifespan=life)
def me(pineapple_session:str|None=Cookie(default=None,alias=settings.cookie)):
 s=security.get_session(pineapple_session)
 if not s:raise HTTPException(401,'Authentication required')
 return s
@app.get('/api/auth/status')
def status(pineapple_session:str|None=Cookie(default=None,alias=settings.cookie)):
 s=security.get_session(pineapple_session);return {'setup_required':security.setup_required(),'authenticated':bool(s)}
@app.post('/api/auth/setup')
def setup(x:Cred,r:Response):
 try:uid=security.create_admin(x.username,x.password)
 except ValueError as e:raise HTTPException(400,str(e))
 t=security.new_session(uid);r.set_cookie(settings.cookie,t,httponly=True,samesite='strict');return {'ok':True}
@app.post('/api/auth/login')
def login(x:Cred,r:Response):
 u=security.verify(x.username,x.password)
 if not u:raise HTTPException(401,'Invalid credentials')
 r.set_cookie(settings.cookie,security.new_session(u['id']),httponly=True,samesite='strict');return {'ok':True}
@app.post('/api/auth/logout')
def logout(r:Response,pineapple_session:str|None=Cookie(default=None,alias=settings.cookie)):
 security.revoke(pineapple_session);r.delete_cookie(settings.cookie);return {'ok':True}
@app.get('/api/tools/health')
def health(u=Depends(me)):return {'items':tools.health()}
@app.post('/api/tools/run')
def runjob(x:Job,u=Depends(me)):
 try:return tools.run(x.tool_id,x.config,u['user_id'],x.session_id)
 except (ValueError,KeyError) as e:raise HTTPException(400,str(e))
@app.post('/api/authorization/demo')
def authdemo(x:Authz,u=Depends(me)):
 sid=secrets.token_urlsafe(12);raw=json.dumps(x.model_dump(),sort_keys=True);h=hashlib.sha256(raw.encode()).hexdigest()
 with connect() as d:d.execute('INSERT INTO authorization_sessions VALUES(?,?,?,?,?,?)',(sid,'ACTIVE',x.expires_at,json.dumps(x.tools),json.dumps(x.targets),h))
 return {'session_id':sid,'snapshot_hash':h}
@app.get('/api/jobs')
def jobs(u=Depends(me)):
 with connect() as d:return {'items':[dict(x) for x in d.execute('SELECT * FROM tool_jobs ORDER BY created_at DESC LIMIT 100')]}
@app.get('/healthz')
def healthz():return {'status':'ok','version':settings.version}
app.mount('/assets',StaticFiles(directory=settings.frontend/'assets'),name='assets')
@app.get('/{path:path}',include_in_schema=False)
def spa(path=''):return FileResponse(settings.frontend/'index.html')
