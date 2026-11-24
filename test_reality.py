import unittest
from test_app import ApiTests
from reality import stress_scenario, qubo_problem

class RealityMathTests(unittest.TestCase):
 def test_stress_reproducible_and_zero_volatility(self):
  s={'allocation':{'growth':50,'resilience':30,'reserve':20}}
  args={'baseline':0,'volatility':0,'seed':42,'samples':100,'growth_shock':-20}
  a=stress_scenario(s,args,0); self.assertEqual(a,stress_scenario(s,args,0)); self.assertAlmostEqual(a['mean'],-2.2); self.assertEqual(a['p10'],a['p90']); self.assertEqual(a['loss_probability'],1)
 def test_invalid_stress(self):
  with self.assertRaises(ValueError): stress_scenario({'allocation':{'growth':50,'resilience':30,'reserve':20}},{'volatility':-1},0)
 def test_qubo_penalizes_invalid_states(self):
  p=qubo_problem([{'id':1,'score':90},{'id':2,'score':70},{'id':3,'score':100}]); n=len(p['linear']); energies=[]
  for mask in range(1<<n):
   bits=[(mask>>i)&1 for i in range(n)]; e=p['offset']+sum(x*b for x,b in zip(p['linear'],bits))+sum(q['bias']*bits[q['i']]*bits[q['j']] for q in p['quadratic']); energies.append((e,mask))
  self.assertEqual(min(energies)[1],4)

class RealityApiTests(unittest.TestCase):
 setUp=ApiTests.setUp; tearDown=ApiTests.tearDown; req=ApiTests.req; login=ApiTests.login
 def test_stress_and_export(self):
  self.login(); rid=self.req('/api/runs','POST',{})[1]['id']; self.assertEqual(self.req(f'/api/reality/{rid}/stress','POST',{'scenario_id':1})[0],200); self.assertEqual(self.req(f'/api/reality/{rid}/qubo')[0],200); self.assertEqual(self.req(f'/api/reality/{rid}/stress','POST',{'scenario_id':999})[0],400)
 def test_plan_quota_and_role(self):
  self.login(); uid=self.req('/api/me')[1]['user']['id']; self.assertEqual(self.req(f'/api/owner/plans/{uid}','PATCH',{'plan':'explorer','limit':1})[0],200); self.assertEqual(self.req('/api/runs','POST',{})[0],201); self.assertEqual(self.req('/api/runs','POST',{})[0],429); self.assertEqual(self.req('/api/entitlement')[1]['remaining'],0)
  self.req('/api/owner/users','POST',{'email':'analyst@example.test','password':'StrongPass123!','role':'analyst'}); self.req('/api/logout','POST',{}); self.login('analyst@example.test'); self.assertEqual(self.req(f'/api/owner/plans/{uid}','PATCH',{'plan':'enterprise','limit':0})[0],403)
 def test_independent_review_and_revocation(self):
  self.login(); uid=self.req('/api/me')[1]['user']['id']; rid=self.req('/api/runs','POST',{})[1]['id']; other=self.req('/api/owner/users','POST',{'email':'exec@example.test','password':'StrongPass123!','role':'executive'})[1]['id']; wid=self.req('/api/owner/workspaces','POST',{'name':'Review team'})[1]['id']; path=f'/api/reviews/{wid}/{rid}'
  for member in (uid,other): self.req(f'/api/owner/workspaces/{wid}/members','POST',{'user_id':member})
  self.req(f'/api/workspaces/{wid}/shares','POST',{'run_id':rid}); self.assertEqual(self.req(path,'POST',{'decision':'approve','note':'Self review'})[0],403)
  self.req('/api/logout','POST',{}); self.login('exec@example.test'); self.assertEqual(self.req(path,'POST',{'decision':'approve','note':'Reviewed assumptions'})[0],201); self.assertEqual(self.req(path)[1]['reviews'][0]['decision'],'approve'); self.req('/api/logout','POST',{}); self.login(); self.req(f'/api/owner/workspaces/{wid}/members','DELETE',{'user_id':other}); self.assertEqual(self.req(path)[1]['reviews'][0]['decision'],'approve'); self.req('/api/logout','POST',{}); self.login('exec@example.test'); self.assertEqual(self.req(path)[0],404)
del ApiTests
