# Render Free evaluation deployment

Only synthetic data. SQLite is ephemeral: accounts, MFA enrollment, decisions, workspaces and backups can disappear on idle spin-down, restart or redeploy. Keep the owner bootstrap environment variables configured privately to recreate the owner after a reset. Never commit secrets. This is not production hosting.

1. Upload the extracted contents of this directory to the root of https://github.com/Khuxaeper1105/Cogninextus (main branch). The archive itself is not the source tree. Do not commit data, environment files or credentials.
2. Open https://dashboard.render.com/blueprints and create a Blueprint from that repository. Check that only one Free web service and no paid disk or other resource is selected.
3. Supply COGNI_OWNER_EMAIL and COGNI_OWNER_PASSWORD (12+ characters, unique) in Render privately. Do not share them in chat.
4. Deploy. Verify /api/health, sign in, and use synthetic data only. No real financial data or customer accounts. Free-tier usage limits apply.

Manual service configuration: Python, main, Frankfurt, Free; build `pip install -r requirements-production.txt && python -m unittest discover -s tests -q`; start `python production.py`; health path `/api/health`. Set HOST=0.0.0.0, COGNI_SECURE_COOKIE=1, COGNI_DB=/tmp/cogninexus/cogni.sqlite, and the two owner variables privately.

Reference: https://render.com/docs/free
