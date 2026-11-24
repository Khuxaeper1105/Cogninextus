import unittest, time
from test_app import ApiTests
from sovereign import totp, matching_step

class TotpTests(unittest.TestCase):
 def test_rfc_vector(self):
  self.assertEqual(totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ',1),'287082')
 def test_replay_and_window(self):
  key='GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
  self.assertEqual(matching_step(key,totp(key,100),3000,-1),100)
  self.assertIsNone(matching_step(key,totp(key,100),3000,100))
  self.assertIsNone(matching_step(key,totp(key,97),3000,-1))

class SecurityTests(unittest.TestCase):
 setUp=ApiTests.setUp; tearDown=ApiTests.tearDown; req=ApiTests.req; login=ApiTests.login
 def enroll(self):
  self.login(); code,r=self.req('/api/security/mfa/start','POST',{'password':'StrongPass123!'})
  self.assertEqual(code,200); key=r['secret']; otp=totp(key,int(time.time())//30)
  code,r=self.req('/api/security/mfa/enable','POST',{'code':otp}); self.assertEqual(code,200)
  return key,r['recovery_codes']
 def test_mfa_requires_second_factor_and_recovery_is_single_use(self):
  key,codes=self.enroll(); self.req('/api/logout','POST',{}); self.assertEqual(self.login()[0],401)
  self.assertEqual(self.req('/api/login','POST',{'email':'owner@example.test','password':'StrongPass123!','code':codes[0]})[0],200)
  self.req('/api/logout','POST',{}); self.assertEqual(self.req('/api/login','POST',{'email':'owner@example.test','password':'StrongPass123!','code':codes[0]})[0],401)
 def test_enrollment_requires_password(self):
  self.login(); self.assertEqual(self.req('/api/security/mfa/start','POST',{'password':'wrong'})[0],403)
 def test_enrollment_wrong_code(self):
  self.login(); self.req('/api/security/mfa/start','POST',{'password':'StrongPass123!'}); self.assertEqual(self.req('/api/security/mfa/enable','POST',{'code':'bad'})[0],400)
 def test_mfa_disable_requires_second_factor(self):
  key,codes=self.enroll(); self.assertEqual(self.req('/api/security/mfa/disable','POST',{'password':'StrongPass123!','code':'bad'})[0],403)
  self.assertEqual(self.req('/api/security/mfa/disable','POST',{'password':'StrongPass123!','code':codes[0]})[0],200)
  self.assertFalse(self.req('/api/security')[1]['mfa_enabled'])
 def test_revoke_other_sessions(self):
  self.login(); old=self.cookie; self.login(); new=self.cookie
  self.assertEqual(self.req('/api/security/revoke','POST',{})[0],200); self.cookie=old
  self.assertEqual(self.req('/api/me')[0],401); self.cookie=new; self.assertEqual(self.req('/api/me')[0],200)
 def test_owner_metrics_permissions(self):
  self.login(); self.assertEqual(self.req('/api/owner/security')[1]['mfa_enabled_accounts'],0)
  self.req('/api/owner/users','POST',{'email':'analyst@example.test','password':'StrongPass123!','role':'analyst'}); self.login('analyst@example.test'); self.assertEqual(self.req('/api/owner/security')[0],403)
del ApiTests
