import unittest,tempfile,os,json,io
from app import App
class ApiTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.app=App(os.path.join(self.tmp.name,'db.sqlite'), 'owner@example.test','StrongPass123!'); self.cookie=''; self.csrf=''
 def tearDown(self): self.tmp.cleanup()
 def req(self,path,method='GET',data=None):
  body=json.dumps(data).encode() if data is not None else b''; info={}
  env={'PATH_INFO':path,'REQUEST_METHOD':method,'wsgi.input':io.BytesIO(body),'CONTENT_LENGTH':str(len(body)),'CONTENT_TYPE':'application/json','HTTP_COOKIE':self.cookie,'HTTP_X_CSRF_TOKEN':self.csrf,'REMOTE_ADDR':'127.0.0.1'}
  def start(s,h): info.update(status=int(s.split()[0]),headers=dict(h))
  result=json.loads(b''.join(self.app(env,start)))
  if 'Set-Cookie' in info['headers']: self.cookie=info['headers']['Set-Cookie'].split(';')[0]
  if 'csrf' in result: self.csrf=result['csrf']
  return info['status'],result
 def login(self,email='owner@example.test',password='StrongPass123!'): return self.req('/api/login','POST',{'email':email,'password':password})
 def test_access(self):
  self.assertEqual(self.req('/api/owner')[0],401); self.assertEqual(self.login()[0],200); self.assertEqual(self.req('/api/owner')[0],200)
 def test_persistence_and_feedback(self):
  self.login(); code,r=self.req('/api/runs','POST',{}); self.assertEqual(code,201); rid=r['id']; self.assertEqual(len(self.req('/api/runs')[1]['runs']),1)
  self.assertEqual(self.req(f'/api/runs/{rid}/feedback','POST',{'scenario_id':1,'actual':25})[0],201)
  self.assertEqual(self.req(f'/api/runs/{rid}/feedback','POST',{'scenario_id':1,'actual':25})[0],409)
  self.assertNotEqual(self.req('/api/runs','POST',{})[1]['result']['calibration'],0)
 def test_role_and_isolation(self):
  self.login(); rid=self.req('/api/runs','POST',{})[1]['id']; self.assertEqual(self.req('/api/owner/users','POST',{'email':'analyst@example.test','password':'StrongPass123!','role':'analyst'})[0],201)
  self.req('/api/logout','POST',{}); self.login('analyst@example.test'); self.assertEqual(self.req('/api/owner')[0],403); self.assertEqual(self.req(f'/api/runs/{rid}')[0],404)
 def test_csrf(self):
  self.login(); self.csrf=''; self.assertEqual(self.req('/api/runs','POST',{})[0],403)
 def test_owner_cannot_disable_self(self):
  self.login(); uid=self.req('/api/me')[1]['user']['id']; self.assertEqual(self.req(f'/api/owner/users/{uid}','PATCH',{'active':False})[0],400)
