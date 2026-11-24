"""Optional provider and operational tools; no remote calls by default."""
import argparse, itertools, json, os, sqlite3, urllib.request
from pathlib import Path
from contextlib import closing

def backup_database(source,dest):
    source,dest=Path(source),Path(dest)
    if not source.is_file(): raise FileNotFoundError(source)
    # Reserve without overwriting; remove incomplete file on failure.
    fd=os.open(dest,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600); os.close(fd)
    try:
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(dest)) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise RuntimeError('Backup integrity check failed')
            dst.commit()
    except BaseException:
        dest.unlink(missing_ok=True); raise

def explanation_payload(result):
    return {'method':result['method'],'scope':result['assumptions']['scope'],'scenarios':[{k:s[k] for k in ('id','allocation','score','mean','p10','p90','loss_probability')} for s in result['scenarios']]}

def local_explanation(result,model):
    # Fixed loopback address; no user-supplied URL or automatic upload.
    prompt='Explain the trade-offs in these illustrative model outputs. Distinguish assumptions from evidence. No investment advice, no guaranteed outcomes. Do not invent facts. Data: '+json.dumps(explanation_payload(result))
    data=json.dumps({'model':model,'prompt':prompt,'stream':False,'options':{'num_predict':400}}).encode()
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=data,headers={'Content-Type':'application/json'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(req,timeout=25) as response:
        raw=response.read(131073)
    if len(raw)>131072: raise ValueError('Provider response exceeds limit')
    text=json.loads(raw)['response']
    if not isinstance(text,str) or not text.strip(): raise ValueError('Empty provider response')
    return text[:12000]

def exact_qubo(p):
    n=len(p['linear'])
    if not 1<=n<=8 or len(p['scenario_ids'])!=n: raise ValueError('Invalid QUBO size')
    def energy(bits): return p['offset']+sum(x*b for x,b in zip(p['linear'],bits))+sum(q['bias']*bits[q['i']]*bits[q['j']] for q in p['quadratic'])
    bits=min(itertools.product((0,1),repeat=n),key=energy)
    return {'backend':'classical exhaustive enumeration','bits':bits,'energy':energy(bits),'scenario_id':p['scenario_ids'][bits.index(1)] if sum(bits)==1 else None}

def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='cmd',required=True)
    backup=sub.add_parser('backup'); backup.add_argument('source'); backup.add_argument('destination')
    qubo=sub.add_parser('solve-qubo'); qubo.add_argument('problem')
    args=parser.parse_args()
    if args.cmd=='backup': backup_database(args.source,args.destination); print('Backup created and integrity checked.')
    else: print(json.dumps(exact_qubo(json.loads(Path(args.problem).read_text())),indent=2))
if __name__=='__main__': main()
