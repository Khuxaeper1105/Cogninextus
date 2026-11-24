"""Exact small statevector experiments and explicitly assumed structural models."""
import cmath, math

def quantum_experiment(rows):
    """One-layer QAOA-style diagonal phase + X mixer; candidate index encoding.
    Padded states receive a penalty; this is not a full allocation optimizer.
    """
    n=len(rows)
    if not 1<=n<=8: raise ValueError('Expected 1–8 candidate scenarios')
    qubits=(n-1).bit_length(); size=1<<qubits
    scores=[float(r['score']) for r in rows]; best=max(scores); worst=min(scores)
    scale=max(best-worst,1.0); utility=[(s-worst)/scale for s in scores]+[-1.0]*(size-n)
    def circuit(gamma,beta):
        state=[cmath.exp(1j*gamma*v)/math.sqrt(size) for v in utility]
        c=math.cos(beta); s=-1j*math.sin(beta)
        for bit in range(qubits):
            for i in range(size):
                if i & (1<<bit): continue
                j=i|(1<<bit); a,b=state[i],state[j]; state[i],state[j]=c*a+s*b,s*a+c*b
        p=[abs(a)**2 for a in state]; total=sum(p)
        return [x/total for x in p]
    optimum=None; evaluations=0
    for gi in range(17):
        for bi in range(17):
            gamma=gi*math.pi/8; beta=bi*math.pi/16; p=circuit(gamma,beta); val=sum(x*y for x,y in zip(p,utility)); evaluations+=1
            if optimum is None or val>optimum[0]+1e-12: optimum=(val,gamma,beta,p)
    _,gamma,beta,p=optimum; valid=sum(p[:n]); expected=sum(s*x for s,x in zip(scores,p))/valid if valid>1e-15 else None
    return {'method':'Exact complex statevector / one-layer QAOA-style experiment','qubits':qubits,'gamma':gamma,'beta':beta,'evaluations':evaluations,'reference_score':best,'expected_score':expected,'uniform_expected_score':sum(scores)/n,'optimal_probability':sum(p[i] for i,s in enumerate(scores) if s==best),'invalid_probability':sum(p[n:]),'states':[{'basis':format(i,f'0{max(1,qubits)}b'),'scenario_id':rows[i]['id'] if i<n else None,'score':scores[i] if i<n else None,'probability':p[i]} for i in range(size)],'scope':'Classical statevector emulation of a small quantum circuit over already ranked candidates. Conditional expected score excludes invalid states. No hardware, QFT or demonstrated speedup.'}

CAUSAL_DEFAULT={'training':40,'demand':60,'intervention':75}
def causal_experiment(payload):
    if not isinstance(payload,dict): raise ValueError('Expected an object')
    p={**CAUSAL_DEFAULT,**payload}
    for k in CAUSAL_DEFAULT:
        x=p[k]
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=100: raise ValueError(f'{k} must be between 0 and 100')
    def clamp(v): return max(0,min(100,v))
    def evaluate(training):
        demand=p['demand']; workload=clamp(30+.65*demand-.25*training); retention=clamp(75+.20*training-.40*workload); productivity=clamp(35+.35*training+.20*retention-.15*workload)
        return {'training':training,'demand':demand,'workload':workload,'retention':retention,'productivity':productivity}
    baseline=evaluate(p['training']); intervention=evaluate(p['intervention'])
    return {'baseline':baseline,'intervention':intervention,'effect':{k:intervention[k]-baseline[k] for k in ('workload','retention','productivity')},'edges':[['demand','workload'],['training','workload'],['training','retention'],['workload','retention'],['training','productivity'],['retention','productivity'],['workload','productivity']],'equations':['workload = clip(30 + 0.65 demand − 0.25 training)','retention = clip(75 + 0.20 training − 0.40 workload)','productivity = clip(35 + 0.35 training + 0.20 retention − 0.15 workload)'],'scope':'Assumed deterministic structural equations, not learned causal effects. Values are synthetic indices, not probabilities or employment recommendations.'}
