"""Optional browser smoke test: pip install playwright; playwright install chromium."""
import os,sys,tempfile,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import App
from wsgiref.simple_server import make_server
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 app=App(Path(tmp)/'db.sqlite','owner@example.test','StrongPass123!')
 server=make_server('127.0.0.1',0,app); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or None, args=['--no-sandbox']); page=browser.new_page(viewport={'width':1440,'height':1000}); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   url=f'http://127.0.0.1:{server.server_port}'
   if os.environ.get('COGNI_BROWSER_INTERCEPT')=='1':
    # Isolated browser test transport: no network navigation. Route all app requests
    # through a synthetic origin into the local WSGI server using Python HTTP.
    import http.client
    from urllib.parse import urlsplit
    url='http://cogninexus.test'
    def intercept(route):
     r=route.request; parsed=urlsplit(r.url); conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
     try:
      headers={k:v for k,v in r.all_headers().items() if k.lower() not in ('host','content-length','connection')}; conn.request(r.method,parsed.path+('?' + parsed.query if parsed.query else ''),body=r.post_data_buffer,headers=headers); response=conn.getresponse(); route.fulfill(status=response.status,headers={k:v for k,v in response.getheaders() if k.lower() not in ('connection','transfer-encoding')},body=response.read())
     finally: conn.close()
    page.route('http://cogninexus.test/**',intercept)
   page.goto(url);page.get_by_label('Email',exact=True).fill('owner@example.test');page.get_by_label('Password',exact=True).fill('StrongPass123!');page.get_by_role('button',name='Sign in').click();page.get_by_role('heading',name='Owner dashboard').wait_for()
   page.get_by_label('Email',exact=True).fill('analyst@example.test');page.get_by_label('Temporary password').fill('AnalystPass123!');page.get_by_role('button',name='Create account').click();page.get_by_text('analyst@example.test',exact=True).wait_for()
   if os.environ.get('SCREENSHOT_DIR'): page.screenshot(path=os.path.join(os.environ['SCREENSHOT_DIR'],'CogniNexus-owner.png'),full_page=True)
   page.get_by_role('button',name='Manage plans').click();page.get_by_role('heading',name='Plans & allowances').wait_for();page.locator('form[data-plan]').first.get_by_label('Monthly runs').fill('25');page.locator('form[data-plan]').first.get_by_role('button',name='Save allowance').click();page.get_by_text('Allowance updated',exact=True).wait_for();
   page.get_by_role('button',name='SOLAR lab').click();page.get_by_role('button',name='Run simulation').click();page.get_by_role('heading',name='Probability observatory').wait_for()
   if os.environ.get('SCREENSHOT_DIR'): page.screenshot(path=os.path.join(os.environ['SCREENSHOT_DIR'],'CogniNexus-simulation.png'),full_page=True)
   page.get_by_role('button',name='Quantum experiment').click();page.get_by_role('button',name='Execute quantum circuit').click();page.get_by_role('heading',name='Benchmark interpretation').wait_for()
   page.get_by_role('button',name='Causal laboratory').click();page.get_by_role('button',name='Evaluate intervention').click();page.get_by_role('heading',name='Intervention results').wait_for()
   page.get_by_role('button',name='Owner dashboard').click();page.get_by_role('button',name='Manage workspaces').click();page.get_by_label('Workspace name').fill('Engineering');page.get_by_role('button',name='Create workspace').click();page.get_by_role('heading',name='Engineering',exact=True).wait_for()
   page.get_by_role('row').filter(has_text='owner@example.test').get_by_role('button',name='Add').click();page.get_by_role('row').filter(has_text='owner@example.test').get_by_role('button',name='Remove').wait_for()
   page.get_by_role('row').filter(has_text='analyst@example.test').get_by_role('button',name='Add').click();page.get_by_role('row').filter(has_text='analyst@example.test').get_by_role('button',name='Remove').wait_for()
   page.get_by_role('button',name='Team workspaces').click();page.get_by_role('button',name='Share with workspace').click();page.get_by_role('button',name='Inspect',exact=True).click();page.get_by_role('heading',name='Shared result',exact=False).wait_for();page.get_by_role('heading',name='Independent review register').wait_for()
   page.get_by_role('button',name='Decision vault').click();page.get_by_role('button',name='View',exact=False).last.click();page.get_by_role('heading',name='Probability observatory').wait_for()
   page.get_by_role('button',name='Reality chamber',exact=False).last.click();page.get_by_role('heading',name='Reality chamber').wait_for();page.locator('input[data-camera=yaw]').fill('60');page.get_by_label('Growth shock (percentage points)').fill('-15');page.get_by_role('button',name='Run stress test').click();page.get_by_text('Stress mean',exact=True).wait_for();page.get_by_role('button',name='Back to simulation').click();page.get_by_label('Actual realized return').fill('20');page.get_by_role('button',name='Record outcome').click();page.get_by_text('Recorded outcome:',exact=False).wait_for()
   page.get_by_role('button',name='Decision vault').click();page.get_by_text('Growth under uncertainty',exact=True).wait_for();page.set_viewport_size({'width':390,'height':844});page.get_by_role('button',name='SOLAR lab').click();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
   page.get_by_role('button',name='Sign out').last.click();page.get_by_label('Email',exact=True).fill('analyst@example.test');page.get_by_label('Password',exact=True).fill('AnalystPass123!');page.get_by_role('button',name='Sign in').click();page.get_by_role('heading',name='Explore the futures you can influence.').wait_for();assert page.get_by_role('button',name='Owner dashboard').count()==0
   page.get_by_role('button',name='Team workspaces').click();page.get_by_role('button',name='Inspect',exact=True).click();page.get_by_role('heading',name='Shared result',exact=False).wait_for();page.get_by_role('heading',name='Independent review register').wait_for();assert not errors,errors;browser.close();print('Browser smoke: PASS (desktop, mobile layout, owner, analyst, simulation, feedback, vault, reality)')
 finally: server.shutdown();server.server_close()
