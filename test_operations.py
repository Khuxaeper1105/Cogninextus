import unittest,tempfile,sqlite3
from pathlib import Path
from test_app import ApiTests
from operations import backup_database, explanation_payload, exact_qubo
class OperationsTests(unittest.TestCase):
 def test_backup_is_consistent_and_refuses_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'a.sqlite'; dest=Path(tmp)/'b.sqlite'
   with sqlite3.connect(source) as c: c.execute('CREATE TABLE items(id INTEGER)'); c.execute('INSERT INTO items VALUES(42)')
   backup_database(source,dest)
   with sqlite3.connect(dest) as c: self.assertEqual(c.execute('SELECT id FROM items').fetchone()[0],42)
   with self.assertRaises(FileExistsError): backup_database(source,dest)
 def test_summary_excludes_names_and_budget(self):
  from engine import simulate
  r=simulate({'name':'Confidential name','budget':4321}); p=explanation_payload(r)
  self.assertNotIn('Confidential name',str(p)); self.assertNotIn('4321',str(p)); self.assertIn('scenarios',p)
 def test_exact_provider_reference(self):
  from reality import qubo_problem
  p=qubo_problem([{'id':7,'score':20},{'id':8,'score':40}]); self.assertEqual(exact_qubo(p)['scenario_id'],8)
class OptionalApiTests(unittest.TestCase):
 setUp=ApiTests.setUp; tearDown=ApiTests.tearDown; req=ApiTests.req; login=ApiTests.login
 def test_ai_disabled_by_default(self):
  from unittest.mock import patch
  import os
  with patch.dict(os.environ,{'COGNI_OLLAMA_MODEL':''}):
   self.login(); rid=self.req('/api/runs','POST',{})[1]['id']; self.assertEqual(self.req('/api/providers')[1]['ai']['enabled'],False); self.assertEqual(self.req(f'/api/reality/{rid}/explain','POST',{})[0],503)
 def test_ai_requires_explicit_consent(self):
  from unittest.mock import patch
  import os
  with patch.dict(os.environ,{'COGNI_OLLAMA_MODEL':'test-model'}):
   self.login(); rid=self.req('/api/runs','POST',{})[1]['id']; self.assertEqual(self.req(f'/api/reality/{rid}/explain','POST',{})[0],400)
   with patch('app.local_explanation',return_value='Unvalidated explanation') as call:
    code,r=self.req(f'/api/reality/{rid}/explain','POST',{'consent':True}); self.assertEqual(code,200); self.assertEqual(r['text'],'Unvalidated explanation'); self.assertTrue(call.called)
del ApiTests
