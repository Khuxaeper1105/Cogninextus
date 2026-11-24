"""Transparent, deterministic classical scenario model. No quantum or causal claims."""
import math, random, statistics
DEFAULT={'name':'Growth under uncertainty','budget':1000000,'weights':[60,30,10],'reserve':20,'growth_cap':70,'volatility':12,'baseline':8,'seed':42,'samples':500}
METHOD='Classical constrained grid search + Monte Carlo'

def validate(payload):
    if not isinstance(payload,dict): raise ValueError('Expected an object')
    p={**DEFAULT,**payload}; out={}
    name=p['name']
    if not isinstance(name,str) or not 1<=len(name.strip())<=120: raise ValueError('Name must contain 1–120 characters')
    out['name']=name.strip()
    for k,lo,hi in [('budget',1,1e12),('reserve',0,100),('growth_cap',0,100),('volatility',0,60),('baseline',-50,50),('seed',0,2147483647),('samples',100,3000)]:
        x=p[k]
        if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not lo<=x<=hi: raise ValueError(f'{k} must be between {lo} and {hi}')
        if k in ('seed','samples') and int(x)!=x: raise ValueError(f'{k} must be an integer')
        out[k]=int(x) if k in ('seed','samples') else float(x)
    w=p['weights']
    if not isinstance(w,list) or len(w)!=3 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=100 for x in w) or sum(w)==0: raise ValueError('Three weights from 0 to 100; at least one positive')
    out['weights']=w
    return out

def clamp(x): return min(100,max(0,x))
def quantile(xs,q):
    n=(len(xs)-1)*q; i=int(n); return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(n-i)

def simulate(payload, calibration=0):
    p=validate(payload); rng=random.Random(p['seed']); w=[x/sum(p['weights']) for x in p['weights']]
    # Explicit illustrative assumptions: reserve earns baseline minus 4, growth baseline plus 16, resilience baseline plus 2.
    shocks=[rng.gauss(0,1) for _ in range(p['samples'])]
    candidates=[]
    # Enumerate a five-percentage-point lattice plus exact constraint boundaries.
    growths=sorted(set([float(x) for x in range(0,101,5) if x<=p['growth_cap']]+[p['growth_cap']]))
    reserves=sorted(set([float(x) for x in range(0,101,5) if x>=p['reserve']]+[p['reserve']]))
    for g in growths:
        for r in reserves:
            h=100-g-r
            if h < -1e-8: continue
            h=max(0,h)
            mu=p['baseline']+.16*g+.02*h-.04*r+calibration
            sigma=p['volatility']*(.18+.010*g+.003*h)
            profit=clamp(50+2*(mu-calibration)) # calibration adjusts forecast, not ranking
            safety=clamp(95-.65*g-.35*p['volatility']+.12*r)
            talent=clamp(45+.55*h+.12*r-.20*g)
            score=sum(a*b for a,b in zip(w,[profit,safety,talent]))
            candidates.append((score,g,h,r,mu,sigma,profit,safety,talent))
    candidates.sort(key=lambda c:(-c[0],c[1],-c[3]))
    # Select best overall plus distinct alternatives from top and individual objective extremes.
    chosen=[candidates[0]]
    for idx in (6,7,8):
        c=max(candidates,key=lambda c:c[idx]);
        if c not in chosen: chosen.append(c)
    for c in candidates:
        if len(chosen)>=6: break
        if c not in chosen and all(abs(c[1]-z[1])+abs(c[2]-z[2])+abs(c[3]-z[3])>=15 for z in chosen): chosen.append(c)
    chosen.sort(key=lambda c:-c[0]); rows=[]
    for i,(score,g,h,r,mu,sigma,profit,safety,talent) in enumerate(chosen):
        vals=sorted(mu+sigma*z for z in shocks)
        rows.append({'id':i+1,'allocation':{'growth':round(g,4),'resilience':round(h,4),'reserve':round(r,4)},'score':round(score,3),'metrics':{'profit':round(profit,2),'safety':round(safety,2),'talent':round(talent,2)},'mean':round(statistics.mean(vals),4),'p10':round(quantile(vals,.1),4),'p50':round(quantile(vals,.5),4),'p90':round(quantile(vals,.9),4),'loss_probability':round(sum(x<0 for x in vals)/len(vals),4),'expected_gain':round(p['budget']*statistics.mean(vals)/100,2),'histogram':[{'return':round(mu+sigma*z,3)} for z in sorted(shocks)[::max(1,len(shocks)//100)]]})
    return {'method':METHOD,'model_version':'1.0.0','inputs':p,'calibration':round(calibration,4),'evaluated':len(candidates),'scenarios':rows,'assumptions':{'growth_premium':16,'resilience_premium':2,'reserve_premium':-4,'shock':'Common standard-normal shocks; assumed, not fitted.','scope':'Illustrative one-period allocation; no market or causal validation.','ranking':'Weighted heuristic scores; forecast calibration is separate.'}}
