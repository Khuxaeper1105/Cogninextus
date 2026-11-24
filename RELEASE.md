# CogniNexus 4.0 — Release and handover

## Local launch

Extract the archive, open a terminal inside `CogniNexus-Sovereign`, and run `python app.py` (Windows: `py app.py`). Create the initial owner credentials, then open http://127.0.0.1:8000. Open Account to enroll MFA. The native local version requires Python 3.10+ and no third-party packages.

## Upgrade and rollback

Stop the old application. Run `python operations.py backup /path/to/old/cogni.sqlite /path/to/backup.sqlite` using a fresh destination. Copy the backup into the new `data/cogni.sqlite` path. Start the new application and check existing account, simulation and workspace records. Roll back only by stopping V4 and restoring the original backup under the old version; do not run two versions on the same database. Protect backups as confidential, including MFA seeds and session data.

## Production candidate configuration

Use one application instance on persistent encrypted storage. Initialize the owner in a controlled environment. Provide secrets via deployment environment, not a repository or image. Remove bootstrap secrets after database creation. Install optional dependencies in a virtual environment and review the resolved versions. Configure an HTTPS reverse proxy and `COGNI_SECURE_COOKIE=1`, set `COGNI_DB` to an absolute persistent location, and run `python production.py`. The production server must not be exposed directly to untrusted HTTP clients. Configure proxy request limits, trusted host routing, backup scheduling and monitoring. Login throttling currently uses the immediate peer address; behind a shared proxy it may throttle multiple clients together. Do not trust arbitrary forwarded IP headers. SQLite is single-instance only.

## Before public launch (not yet cleared)

- Run the browser smoke suite on a permitted desktop/mobile browser environment and test MFA enrollment, recovery and session revocation manually.
- Build and exercise the production image, dependency scanning, TLS, restart persistence, backup restoration and owner bootstrap.
- Perform independent security review, rate-limit and load testing; enforce MFA policy as needed; protect TOTP secrets and design recovery procedures.
- Validate the mathematical models with domain data and independent reviewers. Do not use illustrative returns to make high-stakes decisions without validation.
- Obtain explicit authorization before connecting paid providers, collecting payments or publishing.

## Feature boundaries

Local classical optimization, seeded probability simulation, exact small quantum circuit emulation, assumed causal equations, schematic 3D scenarios, workspace collaboration, reviews and manual plans are implemented. Remote quantum hardware, PostgreSQL, cloud AI, payments, physically calibrated digital twins, WebXR and SSO remain outside the delivered scope. Local Ollama adapter requires separate installation and has not been live-tested.
