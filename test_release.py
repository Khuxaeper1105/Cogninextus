import unittest, tempfile, sqlite3, os
from unittest.mock import patch
from pathlib import Path
from app import App
from production import settings
class ReleaseTests(unittest.TestCase):
 def test_production_requires_secure_cookies_and_persistence(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(RuntimeError): settings()
  with patch.dict(os.environ,{'COGNI_SECURE_COOKIE':'1'},clear=True):
   with self.assertRaises(RuntimeError): settings()
  with patch.dict(os.environ,{'COGNI_SECURE_COOKIE':'1','COGNI_DB':'/persistent/data.sqlite'},clear=True): self.assertEqual(settings()['port'],8000)
 def test_additive_migration_keeps_existing_records(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'data.sqlite'; a=App(db,'owner@example.test','StrongPass123!')
   with a.connect() as c:
    c.execute("INSERT INTO runs(user_id,name,result,created) VALUES(1,'Legacy','{}',1)")
    for table in ('mfa','mfa_pending','recovery'): c.execute('DROP TABLE '+table)
   b=App(db)
   with b.connect() as c:
    self.assertEqual(c.execute('SELECT name FROM runs').fetchone()[0],'Legacy'); self.assertEqual(c.execute('SELECT email FROM users').fetchone()[0],'owner@example.test'); self.assertEqual(c.execute('SELECT COUNT(*) FROM mfa').fetchone()[0],0)
    self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
