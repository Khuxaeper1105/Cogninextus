"""RFC 6238-compatible TOTP and one-use high-entropy recovery codes."""
import base64, hashlib, hmac, secrets, struct, re

def new_secret(): return base64.b32encode(secrets.token_bytes(20)).decode('ascii')
def totp(secret,step):
    digest=hmac.new(base64.b32decode(secret),struct.pack('>Q',step),hashlib.sha1).digest()
    offset=digest[-1]&15
    return f'{(int.from_bytes(digest[offset:offset+4],"big")&0x7fffffff)%1000000:06d}'
def matching_step(secret,code,seconds,last):
    if not isinstance(code,str) or not re.fullmatch(r'[0-9]{6}',code): return None
    step=int(seconds)//30
    for s in (step,step-1,step+1):
        if s>=0 and s>last and hmac.compare_digest(totp(secret,s),code): return s
    return None

def recovery_codes(): return [secrets.token_hex(12) for _ in range(8)]
def recovery_hash(code): return hashlib.sha256(code.encode()).hexdigest()
def consume_factor(c,uid,code,seconds):
    row=c.execute('SELECT secret,last_step FROM mfa WHERE user_id=?',(uid,)).fetchone()
    if not row or not isinstance(code,str) or len(code)>64: return False
    step=matching_step(row['secret'],code,seconds,row['last_step'])
    if step is not None:
        return c.execute('UPDATE mfa SET last_step=? WHERE user_id=? AND last_step<?',(step,uid,step)).rowcount==1
    return c.execute('DELETE FROM recovery WHERE user_id=? AND code_hash=?',(uid,recovery_hash(code))).rowcount==1
