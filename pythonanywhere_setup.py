"""Initialize a CogniNexus evaluation deployment on PythonAnywhere."""
import getpass
import os
from pathlib import Path
import sys
import zipfile


def main():
    os.umask(0o077)
    root = Path(__file__).resolve().parent
    release = root / 'release'
    with zipfile.ZipFile(root / 'CogniNexus-V4-Render-Free.zip') as archive:
        archive.extractall(release)
    data = Path.home() / '.cogninexus' / 'data'
    data.mkdir(parents=True, exist_ok=True)
    db = data / 'cogni.sqlite'
    sys.path.insert(0, str(release))
    from app import App, HTTPError
    try:
        app = App(db, secure=True)
    except RuntimeError:
        email = input('Owner email: ').strip()
        password = getpass.getpass('Owner password (12–128 characters): ')
        if password != getpass.getpass('Confirm password: '):
            raise SystemExit('Passwords do not match. Run setup again.')
        try:
            app = App(db, email, password, secure=True)
        except HTTPError as exc:
            raise SystemExit(exc.msg) from None
    os.chmod(db, 0o600)
    wsgi = ('import os, sys\n'
            f'sys.path.insert(0, {str(release)!r})\n'
            f'os.environ["COGNI_DB"] = {str(db)!r}\n'
            'os.environ["COGNI_SECURE_COOKIE"] = "1"\n'
            'from app import create_app\n'
            'application = create_app()\n')
    target = root / 'pythonanywhere_wsgi_generated.py'
    target.write_text(wsgi, encoding='utf-8')
    print('Owner database initialized. Paste the following into your Web tab WSGI configuration file:\n')
    print(wsgi)
    print('Generated file:', target)


if __name__ == '__main__':
    main()
