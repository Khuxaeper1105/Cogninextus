# CogniNexus — SOVEREIGN INTELLIGENCE 4.0

A runnable full-stack decision-support prototype, with an owner dashboard, team workspaces, local quantum circuit emulation and an assumed structural causal laboratory. Python standard library, SQLite, responsive HTML/CSS/JavaScript. No external API keys or runtime dependencies. **Not a validated financial forecasting system or a production quantum engine.**

## Start locally (Windows, macOS, Linux)

1. Extract the ZIP. Install Python 3.10+ if necessary.
2. Open a terminal in the `CogniNexus-Sovereign` directory.
3. Run `python app.py` (Windows: `py app.py` also works).
4. On first launch, enter your own email and a password of at least 12 characters. The password is not echoed. There are no default credentials.
5. Open http://127.0.0.1:8000 and sign in. The owner dashboard opens automatically. Create analyst or executive accounts from there.

Stop with Ctrl+C. Restart using the same command; data remains in `data/cogni.sqlite`. Use the backup command below; keep backups confidential.

## Docker (local)

Set owner credentials before first start, without committing them. PowerShell example:

```powershell
$env:COGNI_OWNER_EMAIL = 'owner@yourdomain.com'
$env:COGNI_OWNER_PASSWORD = Read-Host 'Choose owner password'
docker compose up --build
```

Open http://127.0.0.1:8000. The compose file binds to loopback and uses a persistent Docker volume. Docker Desktop needs working virtualization on Windows. Remove the bootstrap variables after initialization; the database retains the owner hash. Do not use `docker compose down -v` unless you intend to erase data.

## Features

- Owner dashboard: platform counts, account provisioning, role changes, disable/enable, session revocation and recent audit export.
- Executive/analyst command centers: personal decision history, SOLAR lab, model observatory, reality chamber and account settings.
- Constrained classical allocation grid, normalized objectives, seeded Monte Carlo, percentile intervals, empirical loss frequency, illustrative expected gain and comparison of selected feasible alternatives.
- JSON and simple two-line CSV parameter import, JSON/CSV simulation export, persistent outcome feedback, bounded calibration and internal status tracking for executives/owner.
- PBKDF2 salted password hashes, server-side hashed session tokens, 12-hour expiry, HttpOnly SameSite cookies, CSRF enforcement, role checks, per-user simulation isolation, login throttling, parameterized SQL and CSP.

## Input file

JSON example: see `example-decision.json`. CSV: one header and one unquoted row; do not include commas in the name. For weights use `profit_weight,risk_weight,talent_weight`.

## Testing

```sh
python -m unittest discover -s tests -v
node --check static/app.js
```

Optional real browser smoke: install `playwright`, run `playwright install chromium`, then `python tests/browser_smoke.py`. Set `CHROMIUM_PATH` to an alternate Chromium executable if needed. The test creates and removes its own temporary database. `SCREENSHOT_DIR` optionally saves screenshots. See TESTING.md for actual verification results.

## Architecture & limitations

`app.py`: WSGI API, auth, database and static serving. `engine.py`: deterministic allocation model. `horizon.py`: exact small statevector circuit and structural causal intervention experiments. `static/`: UI. `tests/`: automated tests. The owner sees aggregate counts and audit metadata, not other users' private simulation inputs. The executive role marks only its own runs; independent advisory reviews are available for shared runs, separately from personal status. The SOLAR implementation is a classical single-period heuristic model with illustrative assumptions. Reality Chamber includes a rotatable CSS 3D allocation schematic and fixed-allocation stress testing. No learned causal discovery, QFT, quantum hardware, immersive VR/AR, live financial data, payments or autonomous real-world action is implemented. No ROI or future outcomes are guaranteed. Do not use the model for consequential financial or employment decisions without independent validation.

## Deployment boundary

The built-in WSGI server is for local evaluation only. For external access, use a production WSGI server behind HTTPS, configure `COGNI_SECURE_COOKIE=1`, persistent storage, backups, secrets management, monitoring, rate limiting and a security review. The app does not currently implement MFA, password recovery, enterprise SSO, full enterprise tenant isolation, immutable audit storage, PostgreSQL or production billing. Team workspaces provide explicit member-scoped sharing, not separate enterprise tenants. `HOST`, `PORT`, `COGNI_DB`, `COGNI_OWNER_EMAIL`, `COGNI_OWNER_PASSWORD`, `COGNI_SECURE_COOKIE` are environment variables. No external deployment has been performed.


## Upgrading from GENESIS 1.0

Stop the old server. Back up the old `data/cogni.sqlite` file (with the server stopped), extract V3 to a new directory, then copy the database into the new directory at `data/cogni.sqlite`. Alternatively set `COGNI_DB` to the existing database path. V3 adds workspace, entitlement and review tables as needed without dropping or replacing existing data. Continue using the same credentials. For Docker, keep the original named volume or explicitly configure the existing volume; do not run two versions on one database. Keep the backup for rollback, as V1 does not understand V2 collaboration data.

## V2 research modules

- **Quantum Horizon:** choose a saved personal simulation, run a one-layer QAOA-style circuit emulated by exact complex statevectors (up to three qubits; 289 deterministic parameter pairs). Candidate indices encode already-ranked feasible alternatives; unused basis states receive a penalty. Reports exact measurement probabilities, classical reference maximum, conditional expected utility, uniform valid-candidate baseline and invalid-state probability. The classical optimizer still produces the operational allocations. This is a small quantum algorithm simulation, not quantum hardware or quantum advantage.
- **Causal Laboratory:** alter training intensity while holding demand fixed, inspect a directed graph and structural equations, and compare baseline versus intervention workload, retention and productivity indices. Equations are assumed, not estimated from observed data. No causal identification or learned latent variables. Both research labs export JSON.
- **Team workspaces:** owner creates a named workspace and explicitly adds members, including the owner if desired. Users can publish their own saved simulation to a workspace, inspect other members' shared results read-only, and unshare their own runs. Inputs and results become visible to all current and future members while shared. Feedback remains private. Removing a member revokes their access and removes their published shares from that workspace. Prior exports cannot be recalled. Owner administration does not automatically grant access to private runs. No external email invites. V3 adds independent advisory reviews for shared decisions.

## Deployment preparation

The Docker image includes a health check; Docker Compose remains loopback-bound. A GitHub Actions workflow is provided for unit tests, JS syntax and browser smoke tests. Neither Docker nor CI was executed in this build environment. For a Unix production WSGI deployment, install Gunicorn in a managed virtual environment, initialize with `COGNI_OWNER_EMAIL` and `COGNI_OWNER_PASSWORD`, and use `gunicorn --workers 1 --bind 127.0.0.1:8000 'app:create_app()'` behind an HTTPS reverse proxy with `COGNI_SECURE_COOKIE=1`. Keep SQLite on persistent storage and use one worker for initial bootstrap. This command is provided as a deployment example, not a tested production configuration. Do not publish until browser, deployment, load and security tests pass. PostgreSQL migration remains a separate future milestone.


## V3 — Reality Nexus

- **Reality Chamber:** use the orbit, tilt and zoom sliders on a selected saved allocation; adjust baseline return, volatility and growth-specific shock, then run a seeded stress experiment. P10/P90 and loss frequency are conditional on hypothetical assumptions. Stress experiments are not saved as separate runs; export JSON to retain a record. The 3D model is schematic CSS, not a calibrated physical digital twin or WebXR.
- **Quantum interchange:** run a Quantum Horizon experiment and export the one-hot QUBO JSON. Its energy is `-sum(score_i * x_i) + P * (sum(x_i)-1)^2`. Use `python operations.py solve-qubo cogninexus-qubo.json` for the exact classical reference. External annealers can consume the linear/quadratic coefficients and offset via a provider-specific adapter; no hardware job is submitted by this release.
- **Owner plans:** open Plans & allowances, select an account and set a plan label and monthly run limit (zero = unlimited). Quotas count saved classical runs in the UTC calendar month; stress/causal/quantum experiments are not metered. New and migrated accounts default to unassigned/unlimited. Labels have no automatic billing, payment or role effects. Quotas are enforced by the server under a SQLite write transaction.
- **Independent review register:** publish a personal simulation to a workspace. A different member with an executive or owner role can record approve/reject/request-changes with a required note. Reviews are append-only through the application API, visible to current members while the run is shared, retained after revocation, and distinct from personal decision status. No execution or formal sign-off is triggered.
- **Optional local AI:** install and run Ollama independently on the same host at `127.0.0.1:11434`, and set `COGNI_OLLAMA_MODEL` to an installed model name before starting CogniNexus. In PowerShell: `$env:COGNI_OLLAMA_MODEL = 'your-installed-model'`. Open a saved run's Reality Chamber and explicitly request an explanation. Only numerical scenario summaries and method/scope go to the local service, not account identifiers, decision names or budgets. Output is unvalidated, escaped plain text, and not a recommendation. Disabled by default; unavailable providers return an error. Live model execution has not been tested. This adapter targets native host execution, not the default Docker container. No cloud AI API is configured.
- **Backup:** `python operations.py backup data/cogni.sqlite data/cogni-backup.sqlite` creates an integrity-checked SQLite snapshot without overwriting an existing file. Store it securely: it contains account hashes, session data and private simulations. To restore, stop the server, retain the current database as a separate backup, replace the database with the selected snapshot, and revoke prior sessions if appropriate.

### Upgrade V2 to V3

Stop V2, back it up with the server stopped, extract V3 separately, then copy the old database into `CogniNexus-Reality/data/cogni.sqlite`. V3 creates only additive tables (`entitlements`, `reviews`) and retains previous accounts, sessions, runs, workspaces and shares. Use the same owner credentials. Keep the original backup for rollback. Do not run multiple versions on the same database.

### Remaining enterprise work

SQLite remains the database; PostgreSQL runtime/migrations, real payment processing, actual remote quantum execution, cloud AI, calibrated physical twins, immersive VR/AR, external enterprise integrations, SSO, and independent security and model validation are not included. This is a local evaluation release, not production-certified software.

## V4 final release — Sovereign Intelligence

- Account settings now support optional TOTP MFA (six digits, 30 seconds, SHA-1), manual authenticator enrollment, eight single-use recovery codes, replay rejection and revocation of other sessions. Save recovery codes securely offline; there is no email recovery. After enrolling, wait for a fresh authenticator code before logging in again. The enrollment code cannot be reused.
- Owner dashboard shows MFA coverage, session counts, workspace counts, review counts and secure-cookie status. Owner and other accounts can enable MFA independently. MFA is optional, not SSO or hardware-backed authentication.
- TOTP secrets are stored in SQLite without application-level encryption. Protect the database and backups with filesystem access restrictions and encrypted storage. Recovery codes are stored as hashes. Do not expose the database or logs publicly.
- Upgrade: stop V3 and create an integrity-checked backup. Copy `data/cogni.sqlite` into the new folder before starting. V4 creates additive MFA tables and indexes. Use the same credentials. Enable MFA after confirming migration.
- `production.py` provides an optional Waitress WSGI entry point. It requires `COGNI_SECURE_COOKIE=1` and explicit `COGNI_DB` persistent path. Install with `python -m pip install -r requirements-production.txt`; place behind a trusted HTTPS reverse proxy. Set `HOST` and `PORT` as appropriate. `Dockerfile.production` packages this configuration separately. The default `Dockerfile` and Compose remain local evaluation configurations. Production dependency install, Docker builds and live hosting were not verified here.
- Consult RELEASE.md for release gates. No public deployment, live payments, or quantum advantage claims are authorized or implied.
