import datetime
import os, json, sqlite3, secrets, hashlib, hmac, time, re, sys, math, getpass
from pathlib import Path
from contextlib import contextmanager
from http.cookies import SimpleCookie
from wsgiref.simple_server import make_server
from engine import simulate, DEFAULT
from horizon import quantum_experiment, causal_experiment
from reality import stress_scenario, qubo_problem
from operations import local_explanation
from sovereign import new_secret, matching_step, recovery_codes, recovery_hash, consume_factor
ROOT=Path(__file__).resolve().parent
ROLES=('owner','executive','analyst')
def password_hash(p,salt=None):
    salt=salt or secrets.token_hex(16); return salt+':'+hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(salt),310000).hex()
def verify(p,stored): return hmac.compare_digest(password_hash(p,stored.split(':')[0]),stored)
def now(): return int(time.time())
def tokenhash(t): return hashlib.sha256(t.encode()).hexdigest()
class HTTPError(Exception):
    def __init__(self,status,msg): self.status=status; self.msg=msg
class App:
    def __init__(self,db,owner_email=None,owner_password=None,secure=False):
        self.db=str(db); self.secure=secure; Path(db).parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL,active INTEGER DEFAULT 1,created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),csrf TEXT,expires INTEGER);
            CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),name TEXT,result TEXT,created INTEGER,status TEXT DEFAULT 'draft');
            CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY,run_id INTEGER UNIQUE REFERENCES runs(id),user_id INTEGER REFERENCES users(id),scenario_id INTEGER,actual REAL,residual REAL,created INTEGER);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,user_id INTEGER,event TEXT,detail TEXT,created INTEGER);
            CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY,count INTEGER,until INTEGER);
            CREATE TABLE IF NOT EXISTS workspaces(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS members(workspace_id INTEGER REFERENCES workspaces(id),user_id INTEGER REFERENCES users(id),PRIMARY KEY(workspace_id,user_id));
            CREATE TABLE IF NOT EXISTS shares(workspace_id INTEGER REFERENCES workspaces(id),run_id INTEGER REFERENCES runs(id),created INTEGER NOT NULL,PRIMARY KEY(workspace_id,run_id));
            CREATE TABLE IF NOT EXISTS entitlements(user_id INTEGER PRIMARY KEY REFERENCES users(id),plan TEXT NOT NULL,run_limit INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,workspace_id INTEGER REFERENCES workspaces(id),run_id INTEGER REFERENCES runs(id),reviewer_id INTEGER REFERENCES users(id),decision TEXT NOT NULL,note TEXT NOT NULL,created INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS mfa(user_id INTEGER PRIMARY KEY REFERENCES users(id),secret TEXT NOT NULL,last_step INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS mfa_pending(user_id INTEGER PRIMARY KEY REFERENCES users(id),secret TEXT NOT NULL,expires INTEGER NOT NULL,session_hash TEXT NOT NULL,tries INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS recovery(user_id INTEGER REFERENCES users(id),code_hash TEXT NOT NULL,PRIMARY KEY(user_id,code_hash));
            CREATE INDEX IF NOT EXISTS runs_user_created ON runs(user_id,created);
            CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id);''')
            if not c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                if not owner_email or not owner_password: raise RuntimeError('First start requires COGNI_OWNER_EMAIL and COGNI_OWNER_PASSWORD, or interactive setup.')
                self.check_user(owner_email,owner_password,'owner'); c.execute('INSERT INTO users(email,password,role,created) VALUES(?,?,?,?)',(owner_email.lower().strip(),password_hash(owner_password),'owner',now()))
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.db,timeout=10); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
        try:
            with c: yield c
        finally: c.close()
    def check_user(self,email,password,role):
        if not isinstance(email,str) or len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email.strip()): raise HTTPError(400,'Enter a valid email')
        if not isinstance(password,str) or not 12<=len(password)<=128: raise HTTPError(400,'Password must be 12–128 characters')
        if role not in ROLES: raise HTTPError(400,'Invalid role')
    def audit(self,c,uid,event,detail=''): c.execute('INSERT INTO audit(user_id,event,detail,created) VALUES(?,?,?,?)',(uid,event,str(detail)[:300],now()))
    def public(self,u): return {k:u[k] for k in ('id','email','role','active','created')}
    def cookie(self,value,age): return ('Set-Cookie',f'cn_session={value}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}'+('; Secure' if self.secure else ''))
    def __call__(self,environ,start):
        headers=[('X-Content-Type-Options','nosniff'),('X-Frame-Options','DENY'),('Referrer-Policy','no-referrer'),('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"),('Cache-Control','no-store')]
        if self.secure: headers.append(('Strict-Transport-Security','max-age=31536000'))
        headers.append(('Permissions-Policy','camera=(), microphone=(), geolocation=()'))
        path=environ.get('PATH_INFO','/'); method=environ.get('REQUEST_METHOD','GET')
        try:
            if path=='/' or path in ('/static/app.js','/static/style.css','/static/icon.svg'):
                if method!='GET': raise HTTPError(405,'Method not allowed')
                f=ROOT/('static/index.html' if path=='/' else path.lstrip('/')); data=f.read_bytes(); typ={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml'}[f.suffix]; status=200
            else:
                with self.connect() as c: status,result,extra=self.route(c,environ,path,method)
                headers+=extra; data=json.dumps(result,allow_nan=False).encode(); typ='application/json; charset=utf-8'
        except HTTPError as e: status=e.status; data=json.dumps({'error':e.msg}).encode(); typ='application/json; charset=utf-8'
        except (ValueError,TypeError,KeyError) as e: status=400; data=json.dumps({'error':str(e)}).encode(); typ='application/json; charset=utf-8'
        except Exception as e:
            print('Internal error:',type(e).__name__,file=sys.stderr); status=500; data=b'{"error":"Internal server error"}'; typ='application/json; charset=utf-8'
        from http import HTTPStatus
        start(f'{status} {HTTPStatus(status).phrase}',headers+[('Content-Type',typ),('Content-Length',str(len(data)))]); return [data]
    def entitlement(self,c,uid):
        row=c.execute('SELECT plan,run_limit FROM entitlements WHERE user_id=?',(uid,)).fetchone()
        plan,limit=(row['plan'],row['run_limit']) if row else ('unassigned',0)
        month=datetime.datetime.now(datetime.timezone.utc).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        used=c.execute('SELECT COUNT(*) FROM runs WHERE user_id=? AND created>=?',(uid,int(month.timestamp()))).fetchone()[0]
        return {'plan':plan,'limit':limit,'used':used,'remaining':max(0,limit-used) if limit else None,'period':month.strftime('%Y-%m'),'billing':'Manual entitlement; no payment processing'}
    def route(self,c,e,path,m):
        body={}; extra=[]
        if m in ('POST','PATCH','DELETE'):
            n=int(e.get('CONTENT_LENGTH') or 0)
            if n<0 or n>100000: raise HTTPError(413,'Request too large')
            if not e.get('CONTENT_TYPE','').startswith('application/json'): raise HTTPError(415,'JSON required')
            body=json.loads(e['wsgi.input'].read(n) or b'{}')
            if not isinstance(body,dict): raise HTTPError(400,'Object required')
        if path=='/api/health' and m=='GET': return 200,{'status':'ok','version':'4.0.0','backend':'classical + statevector simulator'},[]
        if path=='/api/login' and m=='POST':
            c.execute('BEGIN IMMEDIATE')
            email=body.get('email',''); pw=body.get('password','')
            if not isinstance(email,str) or not isinstance(pw,str) or len(email)>254 or len(pw)>128: raise HTTPError(400,'Invalid credentials')
            email=email.lower().strip(); key=e.get('REMOTE_ADDR','unknown'); attempt=c.execute('SELECT * FROM attempts WHERE key=?',(key,)).fetchone()
            if attempt and attempt['until']>now() and attempt['count']>=10: raise HTTPError(429,'Too many attempts; retry in 15 minutes')
            u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
            valid=verify(pw,u['password'] if u else '0'*32+':'+'0'*64)
            if not u or not valid or not u['active'] or (c.execute('SELECT 1 FROM mfa WHERE user_id=?',(u['id'],)).fetchone() and not consume_factor(c,u['id'],body.get('code'),now())):
                count=attempt['count']+1 if attempt and attempt['until']>now() else 1; until=attempt['until'] if attempt and attempt['until']>now() else now()+900
                c.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)',(key,count,until)); c.commit(); raise HTTPError(401,'Invalid credentials')
            c.execute('DELETE FROM attempts WHERE key=?',(key,)); c.execute('DELETE FROM sessions WHERE expires<=?',(now(),)); t=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24)
            c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(tokenhash(t),u['id'],csrf,now()+43200)); self.audit(c,u['id'],'login'); return 200,{'user':self.public(u),'csrf':csrf},[self.cookie(t,43200)]
        cookies=SimpleCookie(); cookies.load(e.get('HTTP_COOKIE','')); t=cookies['cn_session'].value if 'cn_session' in cookies else ''
        u=c.execute('SELECT users.*,sessions.csrf FROM sessions JOIN users ON users.id=sessions.user_id WHERE token=? AND expires>? AND active=1',(tokenhash(t),now())).fetchone()
        if not u: raise HTTPError(401,'Sign in required')
        uid=u['id']; owner=u['role']=='owner'
        if m in ('POST','PATCH','DELETE') and not hmac.compare_digest(e.get('HTTP_X_CSRF_TOKEN',''),u['csrf']): raise HTTPError(403,'Invalid CSRF token')
        if path=='/api/security' and m=='GET':
            return 200,{'mfa_enabled':bool(c.execute('SELECT 1 FROM mfa WHERE user_id=?',(uid,)).fetchone()),'recovery_remaining':c.execute('SELECT COUNT(*) FROM recovery WHERE user_id=?',(uid,)).fetchone()[0],'sessions':c.execute('SELECT COUNT(*) FROM sessions WHERE user_id=? AND expires>?',(uid,now())).fetchone()[0]},[]
        if path=='/api/security/revoke' and m=='POST':
            c.execute('DELETE FROM sessions WHERE user_id=? AND token<>?',(uid,tokenhash(t))); self.audit(c,uid,'other_sessions_revoked'); return 200,{'ok':True},[]
        if path.startswith('/api/security/mfa/') and m=='POST':
            c.execute('BEGIN IMMEDIATE')
            action=path.rsplit('/',1)[-1]; enabled=c.execute('SELECT 1 FROM mfa WHERE user_id=?',(uid,)).fetchone()
            if action in ('start','disable'):
                pw=body.get('password')
                if not isinstance(pw,str) or len(pw)>128 or not verify(pw,u['password']): raise HTTPError(403,'Current password required')
            if action=='start':
                if enabled: raise HTTPError(409,'MFA already enabled')
                key=new_secret(); c.execute('INSERT OR REPLACE INTO mfa_pending VALUES(?,?,?,?,0)',(uid,key,now()+600,tokenhash(t))); return 200,{'secret':key,'expires_in':600},[]
            if action=='enable':
                if enabled: raise HTTPError(409,'MFA already enabled')
                p=c.execute('SELECT * FROM mfa_pending WHERE user_id=? AND expires>? AND session_hash=?',(uid,now(),tokenhash(t))).fetchone()
                if not p or p['tries']>=5: raise HTTPError(400,'Restart enrollment')
                step=matching_step(p['secret'],body.get('code'),now(),-1)
                if step is None:
                    c.execute('UPDATE mfa_pending SET tries=tries+1 WHERE user_id=?',(uid,)); c.commit(); raise HTTPError(400,'Invalid authenticator code')
                codes=recovery_codes(); c.execute('INSERT INTO mfa VALUES(?,?,?)',(uid,p['secret'],step)); c.executemany('INSERT INTO recovery VALUES(?,?)',[(uid,recovery_hash(code)) for code in codes]); c.execute('DELETE FROM mfa_pending WHERE user_id=?',(uid,)); c.execute('DELETE FROM sessions WHERE user_id=? AND token<>?',(uid,tokenhash(t))); self.audit(c,uid,'mfa_enabled'); return 200,{'recovery_codes':codes},[]
            if action=='disable':
                # Reuse the login throttle for failed second-factor checks, scoped to this account.
                key='mfa-disable:'+str(uid); attempt=c.execute('SELECT * FROM attempts WHERE key=?',(key,)).fetchone()
                if attempt and attempt['until']>now() and attempt['count']>=5: raise HTTPError(429,'Retry in 15 minutes')
                if not enabled or not consume_factor(c,uid,body.get('code'),now()):
                    count=attempt['count']+1 if attempt and attempt['until']>now() else 1; until=attempt['until'] if attempt and attempt['until']>now() else now()+900
                    c.execute('INSERT OR REPLACE INTO attempts VALUES(?,?,?)',(key,count,until)); c.commit(); raise HTTPError(403,'Valid second factor required')
                c.execute('DELETE FROM attempts WHERE key=?',(key,)); c.execute('DELETE FROM mfa WHERE user_id=?',(uid,)); c.execute('DELETE FROM recovery WHERE user_id=?',(uid,)); c.execute('DELETE FROM sessions WHERE user_id=? AND token<>?',(uid,tokenhash(t))); self.audit(c,uid,'mfa_disabled'); return 200,{'ok':True},[]
        if path=='/api/me' and m=='GET': return 200,{'user':self.public(u),'csrf':u['csrf']},[]
        if path=='/api/logout' and m=='POST': c.execute('DELETE FROM sessions WHERE token=?',(tokenhash(t),)); self.audit(c,uid,'logout'); return 200,{'ok':True},[self.cookie('',0)]
        if path=='/api/password' and m=='POST':
            if not isinstance(body.get('current'),str) or not verify(body['current'],u['password']): raise HTTPError(400,'Current password incorrect')
            self.check_user(u['email'],body.get('password'),u['role']); c.execute('UPDATE users SET password=? WHERE id=?',(password_hash(body['password']),uid)); c.execute('DELETE FROM sessions WHERE user_id=? AND token<>?',(uid,tokenhash(t))); self.audit(c,uid,'password_changed'); return 200,{'ok':True},[]
        if path=='/api/entitlement' and m=='GET': return 200,self.entitlement(c,uid),[]
        if path=='/api/runs' and m=='GET':
            rows=c.execute('SELECT id,name,created,status FROM runs WHERE user_id=? ORDER BY id DESC LIMIT 200',(uid,)).fetchall(); return 200,{'runs':[dict(r) for r in rows]},[]
        if path=='/api/runs' and m=='POST':
            c.execute('BEGIN IMMEDIATE'); ent=self.entitlement(c,uid)
            if ent['remaining']==0: raise HTTPError(429,'Monthly simulation allowance reached')
            f=c.execute('SELECT COUNT(*) n,COALESCE(SUM(residual),0) total FROM feedback WHERE user_id=?',(uid,)).fetchone(); cal=max(-20,min(20,f['total']/(f['n']+5)))
            result=simulate(body,cal); rid=c.execute('INSERT INTO runs(user_id,name,result,created) VALUES(?,?,?,?)',(uid,result['inputs']['name'],json.dumps(result),now())).lastrowid; self.audit(c,uid,'simulation_created',rid); return 201,{'id':rid,'result':result,'status':'draft','feedback':None},[]
        match=re.fullmatch(r'/api/runs/(\d+)(?:/(feedback|status))?',path)
        if match:
            rid=int(match[1]); r=c.execute('SELECT * FROM runs WHERE id=? AND user_id=?',(rid,uid)).fetchone()
            if not r: raise HTTPError(404,'Run not found')
            result=json.loads(r['result']); f=c.execute('SELECT scenario_id,actual,residual,created FROM feedback WHERE run_id=?',(rid,)).fetchone()
            if not match[2] and m=='GET': return 200,{'id':rid,'result':result,'status':r['status'],'feedback':dict(f) if f else None},[]
            if match[2]=='feedback' and m=='POST':
                if f: raise HTTPError(409,'Feedback already recorded')
                s=next((x for x in result['scenarios'] if x['id']==body.get('scenario_id')),None); a=body.get('actual')
                if not s or isinstance(a,bool) or not isinstance(a,(int,float)) or not math.isfinite(a) or not -100<=a<=1000: raise HTTPError(400,'Select a valid scenario and outcome (-100 to 1000%)')
                # Compare against the original uncalibrated forecast to avoid feedback oscillation.
                residual=a-(s['mean']-result['calibration']); c.execute('INSERT INTO feedback(run_id,user_id,scenario_id,actual,residual,created) VALUES(?,?,?,?,?,?)',(rid,uid,s['id'],a,residual,now())); self.audit(c,uid,'feedback_recorded',rid); return 201,{'ok':True,'residual':residual},[]
            if match[2]=='status' and m=='PATCH':
                if u['role']=='analyst': raise HTTPError(403,'Executive or owner role required')
                status=body.get('status');
                if status not in ('draft','reviewed','approved','archived'): raise HTTPError(400,'Invalid status')
                c.execute('UPDATE runs SET status=? WHERE id=?',(status,rid)); self.audit(c,uid,'run_status',f'{rid}: {status}'); return 200,{'ok':True},[]
        if path=='/api/horizon/causal' and m=='POST': return 200,causal_experiment(body),[]
        qm=re.fullmatch(r'/api/horizon/quantum/(\d+)',path)
        if qm and m=='POST':
            r=c.execute('SELECT result FROM runs WHERE id=? AND user_id=?',(int(qm[1]),uid)).fetchone()
            if not r: raise HTTPError(404,'Run not found')
            return 200,quantum_experiment(json.loads(r['result'])['scenarios']),[]
        if path=='/api/workspaces' and m=='GET':
            return 200,{'workspaces':[dict(x) for x in c.execute('SELECT w.* FROM workspaces w JOIN members m ON w.id=m.workspace_id WHERE m.user_id=? ORDER BY w.name',(uid,))]},[]
        wm=re.fullmatch(r'/api/workspaces/(\d+)/shares(?:/(\d+))?',path)
        if wm:
            wid=int(wm[1]); rid=int(wm[2]) if wm[2] else body.get('run_id')
            if not c.execute('SELECT 1 FROM members WHERE workspace_id=? AND user_id=?',(wid,uid)).fetchone(): raise HTTPError(404,'Workspace not found')
            if not wm[2] and m=='GET':
                return 200,{'shares':[dict(x) for x in c.execute('SELECT r.id,r.name,s.created,r.status,CASE WHEN r.user_id=? THEN 1 ELSE 0 END AS mine FROM shares s JOIN runs r ON r.id=s.run_id WHERE s.workspace_id=? ORDER BY s.created DESC,r.id DESC',(uid,wid))]},[]
            if wm[2] and m=='GET':
                r=c.execute('SELECT r.id,r.result,r.status FROM runs r JOIN shares s ON s.run_id=r.id WHERE s.workspace_id=? AND r.id=?',(wid,rid)).fetchone()
                if not r: raise HTTPError(404,'Shared run not found')
                return 200,{'id':r['id'],'result':json.loads(r['result']),'status':r['status']},[]
            if m in ('POST','DELETE'):
                if type(rid) is not int or not c.execute('SELECT 1 FROM runs WHERE id=? AND user_id=?',(rid,uid)).fetchone(): raise HTTPError(404,'Run not found')
                if m=='POST':
                    c.execute('INSERT OR IGNORE INTO shares(workspace_id,run_id,created) VALUES(?,?,?)',(wid,rid,now())); self.audit(c,uid,'run_shared',f'{wid}: {rid}'); return 201,{'ok':True},[]
                c.execute('DELETE FROM shares WHERE workspace_id=? AND run_id=?',(wid,rid)); self.audit(c,uid,'run_unshared',f'{wid}: {rid}'); return 200,{'ok':True},[]
        if path=='/api/providers' and m=='GET': return 200,{'ai':{'enabled':bool(os.environ.get('COGNI_OLLAMA_MODEL','').strip()),'provider':'Ollama loopback','verified_connection':False},'quantum':{'provider':'QUBO export / local exact statevector','hardware_connected':False}},[]
        rm=re.fullmatch(r'/api/reality/(\d+)/(stress|qubo|explain)',path)
        if rm:
            r=c.execute('SELECT result FROM runs WHERE id=? AND user_id=?',(int(rm[1]),uid)).fetchone()
            if not r: raise HTTPError(404,'Run not found')
            result=json.loads(r['result'])
            if rm[2]=='explain' and m=='POST':
                model=os.environ.get('COGNI_OLLAMA_MODEL','').strip()
                if not model: raise HTTPError(503,'Optional local AI provider is disabled')
                if body.get('consent') is not True: raise HTTPError(400,'Explicit consent required to send scenario summary to the local provider')
                try: text=local_explanation(result,model)
                except Exception: raise HTTPError(503,'Local AI provider unavailable or returned an invalid response')
                self.audit(c,uid,'local_ai_explanation',rm[1]); return 200,{'text':text,'scope':'Unvalidated AI-generated explanation; not a recommendation or forecast.'},[]
            if rm[2]=='qubo' and m=='GET': return 200,qubo_problem(result['scenarios']),[]
            if rm[2]=='stress' and m=='POST':
                sid=body.get('scenario_id'); scenario=next((x for x in result['scenarios'] if type(sid) is int and x['id']==sid),None)
                if not scenario: raise HTTPError(400,'Invalid scenario')
                inputs={k:result['inputs'][k] for k in ('baseline','volatility','seed','samples')}; inputs.update(body)
                return 200,stress_scenario(scenario,inputs,result['calibration']),[]
        rv=re.fullmatch(r'/api/reviews/(\d+)/(\d+)',path)
        if rv:
            wid,rid=map(int,rv.groups()); r=c.execute('SELECT r.user_id FROM runs r JOIN shares s ON r.id=s.run_id JOIN members m ON s.workspace_id=m.workspace_id WHERE s.workspace_id=? AND r.id=? AND m.user_id=?',(wid,rid,uid)).fetchone()
            if not r: raise HTTPError(404,'Shared run not found')
            if m=='GET': return 200,{'reviews':[dict(x) for x in c.execute('SELECT id,reviewer_id,decision,note,created FROM reviews WHERE workspace_id=? AND run_id=? ORDER BY id DESC LIMIT 100',(wid,rid))],'can_review':u['role'] in ('owner','executive') and r['user_id']!=uid},[]
            if m=='POST':
                if u['role']=='analyst' or r['user_id']==uid: raise HTTPError(403,'Independent executive or owner review required')
                decision=body.get('decision'); note=body.get('note')
                if decision not in ('approve','reject','changes') or not isinstance(note,str) or not 1<=len(note.strip())<=1000: raise HTTPError(400,'Valid decision and review note required')
                review=c.execute('INSERT INTO reviews(workspace_id,run_id,reviewer_id,decision,note,created) VALUES(?,?,?,?,?,?)',(wid,rid,uid,decision,note.strip(),now())).lastrowid
                self.audit(c,uid,'independent_review',f'{wid}/{rid}: {decision}'); return 201,{'id':review},[]
        if path.startswith('/api/owner'):
            if not owner: raise HTTPError(403,'Owner role required')
            if path=='/api/owner/security' and m=='GET':
                return 200,{'mfa_enabled_accounts':c.execute('SELECT COUNT(*) FROM mfa').fetchone()[0],'active_sessions':c.execute('SELECT COUNT(*) FROM sessions WHERE expires>?',(now(),)).fetchone()[0],'workspace_count':c.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0],'review_count':c.execute('SELECT COUNT(*) FROM reviews').fetchone()[0],'secure_cookie':self.secure,'owner_mfa':bool(c.execute('SELECT 1 FROM mfa WHERE user_id=?',(uid,)).fetchone())},[]
            if path=='/api/owner/plans' and m=='GET':
                return 200,{'plans':[{'user_id':x['id'],'email':x['email'],**self.entitlement(c,x['id'])} for x in c.execute('SELECT id,email FROM users ORDER BY id')]},[]
            pm=re.fullmatch(r'/api/owner/plans/(\d+)',path)
            if pm and m=='PATCH':
                target=int(pm[1]); plan=body.get('plan'); limit=body.get('limit')
                if not c.execute('SELECT 1 FROM users WHERE id=?',(target,)).fetchone(): raise HTTPError(404,'User not found')
                if plan not in ('unassigned','explorer','professional','enterprise','sovereign') or type(limit) is not int or not 0<=limit<=100000: raise HTTPError(400,'Invalid plan or limit')
                c.execute('BEGIN IMMEDIATE'); c.execute('INSERT INTO entitlements VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET plan=excluded.plan,run_limit=excluded.run_limit',(target,plan,limit)); self.audit(c,uid,'plan_updated',f'{target}: {plan}, {limit}'); return 200,self.entitlement(c,target),[]
            if path=='/api/owner/workspaces':
                if m=='GET':
                    return 200,{'workspaces':[dict(w)|{'members':[x[0] for x in c.execute('SELECT user_id FROM members WHERE workspace_id=?',(w['id'],))]} for w in c.execute('SELECT * FROM workspaces ORDER BY name')]},[]
                if m=='POST':
                    name=body.get('name')
                    if not isinstance(name,str) or not 1<=len(name.strip())<=100: raise HTTPError(400,'Workspace name must contain 1–100 characters')
                    try: wid=c.execute('INSERT INTO workspaces(name,created) VALUES(?,?)',(name.strip(),now())).lastrowid
                    except sqlite3.IntegrityError: raise HTTPError(409,'Workspace already exists')
                    self.audit(c,uid,'workspace_created',wid); return 201,{'id':wid},[]
            mm=re.fullmatch(r'/api/owner/workspaces/(\d+)/members',path)
            if mm and m in ('POST','DELETE'):
                wid=int(mm[1]); target=body.get('user_id')
                if type(target) is not int or not c.execute('SELECT 1 FROM users WHERE id=?',(target,)).fetchone() or not c.execute('SELECT 1 FROM workspaces WHERE id=?',(wid,)).fetchone(): raise HTTPError(404,'Workspace or user not found')
                if m=='POST': c.execute('INSERT OR IGNORE INTO members VALUES(?,?)',(wid,target))
                else:
                    c.execute('DELETE FROM shares WHERE workspace_id=? AND run_id IN (SELECT id FROM runs WHERE user_id=?)',(wid,target))
                    c.execute('DELETE FROM members WHERE workspace_id=? AND user_id=?',(wid,target))
                self.audit(c,uid,'workspace_member_'+('added' if m=='POST' else 'removed'),f'{wid}: {target}'); return 200,{'ok':True},[]
            if path=='/api/owner' and m=='GET':
                counts={k:c.execute(q).fetchone()[0] for k,q in {'users':'SELECT COUNT(*) FROM users','active':'SELECT COUNT(*) FROM users WHERE active=1','runs':'SELECT COUNT(*) FROM runs','feedback':'SELECT COUNT(*) FROM feedback'}.items()}; users=[self.public(x) for x in c.execute('SELECT * FROM users ORDER BY id')]; audit=[dict(x) for x in c.execute('SELECT audit.*,users.email FROM audit LEFT JOIN users ON audit.user_id=users.id ORDER BY audit.id DESC LIMIT 100')]; return 200,{'counts':counts,'users':users,'audit':audit},[]
            if path=='/api/owner/users' and m=='POST':
                email=body.get('email'); pw=body.get('password'); role=body.get('role'); self.check_user(email,pw,role)
                if role=='owner': raise HTTPError(400,'Owner creation is restricted to initial setup')
                try: new=c.execute('INSERT INTO users(email,password,role,created) VALUES(?,?,?,?)',(email.strip().lower(),password_hash(pw),role,now())).lastrowid
                except sqlite3.IntegrityError: raise HTTPError(409,'Email already exists')
                self.audit(c,uid,'user_created',new); return 201,{'id':new},[]
            match=re.fullmatch(r'/api/owner/users/(\d+)',path)
            if match and m=='PATCH':
                target=int(match[1]); active=body.get('active'); role=body.get('role'); row=c.execute('SELECT * FROM users WHERE id=?',(target,)).fetchone()
                if not row: raise HTTPError(404,'User not found')
                if target==uid or row['role']=='owner': raise HTTPError(400,'Owner account cannot be modified here')
                if active is not None and not isinstance(active,bool): raise HTTPError(400,'Active must be boolean')
                if role is not None and role not in ('executive','analyst'): raise HTTPError(400,'Invalid role')
                c.execute('UPDATE users SET active=?,role=? WHERE id=?',(int(active) if active is not None else row['active'],role or row['role'],target)); c.execute('DELETE FROM sessions WHERE user_id=?',(target,)); self.audit(c,uid,'user_updated',target); return 200,{'ok':True},[]
        raise HTTPError(404,'Not found')

def create_app():
    return App(os.environ.get('COGNI_DB',str(ROOT/'data'/'cogni.sqlite')),os.environ.get('COGNI_OWNER_EMAIL'),os.environ.get('COGNI_OWNER_PASSWORD'),os.environ.get('COGNI_SECURE_COOKIE')=='1')

def main():
    db=os.environ.get('COGNI_DB',str(ROOT/'data'/'cogni.sqlite')); email=os.environ.get('COGNI_OWNER_EMAIL'); password=os.environ.get('COGNI_OWNER_PASSWORD')
    try: app=App(db,email,password,os.environ.get('COGNI_SECURE_COOKIE')=='1')
    except RuntimeError:
        if not sys.stdin.isatty(): raise
        print('Create your first owner account.'); email=input('Owner email: '); password=getpass.getpass('Owner password (12+ characters): '); app=App(db,email,password,os.environ.get('COGNI_SECURE_COOKIE')=='1')
    host=os.environ.get('HOST','127.0.0.1'); port=int(os.environ.get('PORT','8000')); print(f'CogniNexus running at http://{host}:{port}',flush=True)
    with make_server(host,port,app) as server: server.serve_forever()
if __name__=='__main__': main()
