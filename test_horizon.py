import unittest, math
from horizon import quantum_experiment, causal_experiment
from engine import simulate

class HorizonTests(unittest.TestCase):
    def test_quantum_probabilities_and_reference(self):
        rows=simulate({})['scenarios']; q=quantum_experiment(rows)
        self.assertAlmostEqual(sum(s['probability'] for s in q['states']),1,places=9)
        self.assertEqual(q['reference_score'],max(s['score'] for s in rows))
        self.assertLessEqual(q['expected_score'],q['reference_score']+1e-9)
        self.assertEqual(q,quantum_experiment(rows))
    def test_quantum_single_feasible(self):
        q=quantum_experiment(simulate({'reserve':100})['scenarios'])
        self.assertEqual(q['optimal_probability'],1)
    def test_causal_intervention_and_identity(self):
        a=causal_experiment({'training':20,'intervention':20})
        self.assertAlmostEqual(a['effect']['retention'],0)
        b=causal_experiment({'training':20,'intervention':80})
        self.assertGreater(b['effect']['retention'],0)
        self.assertEqual(b['baseline']['training'],20)
    def test_causal_input_validation(self):
        for p in [{'training':101},{'intervention':float('nan')},{'demand':True}]:
            with self.assertRaises(ValueError): causal_experiment(p)
