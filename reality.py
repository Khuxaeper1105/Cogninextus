"""Explicit hypothetical stress tests and portable one-hot QUBO formulation."""
import math, random, statistics
from engine import quantile

def stress_scenario(scenario, payload, calibration):
    defaults={'baseline':8,'volatility':12,'growth_shock':0,'seed':42,'samples':500}
    p={**defaults,**payload}
    for k,lo,hi in [('baseline',-50,50),('volatility',0,60),('growth_shock',-100,100),('seed',0,2147483647),('samples',100,3000)]:
        x=p[k]
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not lo<=x<=hi or (k in ('seed','samples') and int(x)!=x): raise ValueError(f'Invalid {k}; expected {lo}–{hi}')
    p={k:p[k] for k in defaults}; p['seed']=int(p['seed']); p['samples']=int(p['samples'])
    a=scenario['allocation']; g,h,r=(a[k] for k in ('growth','resilience','reserve'))
    mu=p['baseline']+.16*g+.02*h-.04*r+calibration+p['growth_shock']*g/100
    sigma=p['volatility']*(.18+.010*g+.003*h); rng=random.Random(p['seed']); vals=sorted(mu+sigma*rng.gauss(0,1) for _ in range(p['samples']))
    return {'inputs':p,'allocation':a,'mean':statistics.mean(vals),'p10':quantile(vals,.1),'p50':quantile(vals,.5),'p90':quantile(vals,.9),'loss_probability':sum(x<0 for x in vals)/len(vals),'method':'Fixed allocation / seeded normal shocks','scope':'Illustrative hypothetical sensitivity, not a market forecast. Growth shock is in percentage points on the growth portion.'}

def qubo_problem(rows):
    if not 1<=len(rows)<=8: raise ValueError('Expected 1–8 scenarios')
    scores=[float(r['score']) for r in rows]; penalty=2*max(1,max(abs(s) for s in scores))+1
    # E = -sum(score_i*x_i) + P*(sum(x_i)-1)^2
    return {'schema':'cogninexus.qubo.v1','scenario_ids':[r['id'] for r in rows],'linear':[-s-penalty for s in scores],'quadratic':[{'i':i,'j':j,'bias':2*penalty} for i in range(len(rows)) for j in range(i+1,len(rows))],'offset':penalty,'reference_scenario_id':rows[scores.index(max(scores))]['id'],'scope':'One-hot selection over precomputed candidates. Not a quantum speedup or hardware result.'}
