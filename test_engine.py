import unittest
from engine import simulate, validate, DEFAULT

class EngineTests(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(simulate(DEFAULT), simulate(DEFAULT))
    def test_feasible(self):
        r=simulate(DEFAULT)
        for s in r['scenarios']:
            self.assertAlmostEqual(sum(s['allocation'].values()),100)
            self.assertGreaterEqual(s['allocation']['reserve'],DEFAULT['reserve'])
            self.assertLessEqual(s['allocation']['growth'],DEFAULT['growth_cap'])
            self.assertLessEqual(s['p10'],s['p50'])
            self.assertLessEqual(s['p50'],s['p90'])
        self.assertEqual(r['method'],'Classical constrained grid search + Monte Carlo')
    def test_weights_change_ranking(self):
        a=simulate({**DEFAULT,'weights':[100,0,0]})
        b=simulate({**DEFAULT,'weights':[0,100,0]})
        self.assertNotEqual(a['scenarios'][0]['allocation'],b['scenarios'][0]['allocation'])
    def test_validation(self):
        for p in [{'weights':[0,0,0]},{'budget':-1},{'reserve':101},{'volatility':float('nan')},{'seed':1.5}]:
            with self.assertRaises(ValueError): validate({**DEFAULT,**p})
    def test_feedback_changes_forecast(self):
        a=simulate(DEFAULT); b=simulate(DEFAULT, calibration=5)
        self.assertAlmostEqual(b['scenarios'][0]['p50']-a['scenarios'][0]['p50'],5,places=2)
