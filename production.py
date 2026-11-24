"""Optional single-instance WSGI deployment behind an HTTPS reverse proxy."""
import os
from app import create_app

def settings():
    if os.environ.get('COGNI_SECURE_COOKIE') != '1':
        raise RuntimeError('Production requires COGNI_SECURE_COOKIE=1 and an HTTPS reverse proxy')
    if not os.environ.get('COGNI_DB'):
        raise RuntimeError('Production requires an explicit persistent COGNI_DB path')
    port=int(os.environ.get('PORT','8000'))
    if not 1<=port<=65535: raise RuntimeError('Invalid port')
    return {'host':os.environ.get('HOST','127.0.0.1'),'port':port,'threads':4,'channel_timeout':60,'max_request_body_size':100000}

def main():
    config=settings()
    try: from waitress import serve
    except ImportError: raise SystemExit('Install optional deployment dependency: python -m pip install -r requirements-production.txt')
    serve(create_app(),**config)
if __name__=='__main__': main()
