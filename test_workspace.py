import unittest
from test_app import ApiTests
class WorkspaceTests(unittest.TestCase):
 setUp=ApiTests.setUp
 tearDown=ApiTests.tearDown
 req=ApiTests.req
 login=ApiTests.login
 def test_shared_access_and_revocation(self):
  self.login(); rid=self.req('/api/runs','POST',{})[1]['id']
  self.req('/api/owner/users','POST',{'email':'analyst@example.test','password':'StrongPass123!','role':'analyst'})
  users=self.req('/api/owner')[1]['users']; uid=next(u['id'] for u in users if u['role']=='analyst'); owner=next(u['id'] for u in users if u['role']=='owner')
  code,w=self.req('/api/owner/workspaces','POST',{'name':'Engineering'}); self.assertEqual(code,201); wid=w['id']
  for u in [uid,owner]: self.assertEqual(self.req(f'/api/owner/workspaces/{wid}/members','POST',{'user_id':u})[0],200)
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares','POST',{'run_id':rid})[0],201)
  self.req('/api/logout','POST',{}); self.login('analyst@example.test')
  self.assertEqual(self.req(f'/api/runs/{rid}')[0],404)
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares/{rid}')[0],200)
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares','POST',{'run_id':rid})[0],404)
  self.req('/api/logout','POST',{}); self.login(); self.assertEqual(self.req(f'/api/owner/workspaces/{wid}/members','DELETE',{'user_id':uid})[0],200)
  self.req('/api/logout','POST',{}); self.login('analyst@example.test'); self.assertEqual(self.req(f'/api/workspaces/{wid}/shares/{rid}')[0],404)
 def test_owner_removal_unshares(self):
  self.login(); rid=self.req('/api/runs','POST',{})[1]['id']; uid=self.req('/api/me')[1]['user']['id']; wid=self.req('/api/owner/workspaces','POST',{'name':'Finance'})[1]['id']
  self.req(f'/api/owner/workspaces/{wid}/members','POST',{'user_id':uid}); self.req(f'/api/workspaces/{wid}/shares','POST',{'run_id':rid})
  self.req(f'/api/owner/workspaces/{wid}/members','DELETE',{'user_id':uid}); self.req(f'/api/owner/workspaces/{wid}/members','POST',{'user_id':uid})
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares/{rid}')[0],404)
  self.assertEqual(self.req(f'/api/runs/{rid}')[0],200)
 def test_share_unshare(self):
  self.login(); rid=self.req('/api/runs','POST',{})[1]['id']; uid=self.req('/api/me')[1]['user']['id']; wid=self.req('/api/owner/workspaces','POST',{'name':'Operations'})[1]['id']; self.req(f'/api/owner/workspaces/{wid}/members','POST',{'user_id':uid})
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares','POST',{'run_id':rid})[0],201)
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares','DELETE',{'run_id':rid})[0],200)
  self.assertEqual(self.req(f'/api/workspaces/{wid}/shares/{rid}')[0],404)
 def test_horizon_routes(self):
  self.assertEqual(self.req('/api/horizon/causal','POST',{})[0],401)
  self.login(); self.assertEqual(self.req('/api/horizon/causal','POST',{})[0],200)
  rid=self.req('/api/runs','POST',{})[1]['id']; self.assertEqual(self.req(f'/api/horizon/quantum/{rid}','POST',{})[0],200)
# Avoid importing base tests twice in discovery.
del ApiTests
