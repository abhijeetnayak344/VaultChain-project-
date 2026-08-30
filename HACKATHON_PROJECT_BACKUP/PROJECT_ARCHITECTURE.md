# AICTE SecureDC — Project Architecture

**Product:** AICTE SecureDC – Blockchain Enabled Cybersecurity & Data Center Management Portal  
**Phase:** 8 — scaffold + identity/RBAC + dashboard + servers + firewalls + audit logging + Fabric anchoring + blockchain verification  
**Status:** Auth, dashboard, server CRUD, firewall approval, security audit logs, Fabric hash anchoring, and blockchain integrity verification are implemented. License/asset modules are not.

This document is the source of truth for structure, boundaries, and how later phases attach. It matches the issued Phase 1 prompt (Django + React + PostgreSQL + Docker). Remaining DCIM modules (licenses, assets) are not implemented yet.

## 1. Goals

- One repository for frontend, backend, database config, and Compose.
- Clear app boundaries so each later module lands in one Django app and one React feature folder.
- Versioned HTTP API (`/api/v1/`) with a stable error envelope and pagination.
- 12-factor configuration via environment variables.
- Dev and production Docker images without baking secrets into the image.

## 2. System context

```text
Browser
   │
   ▼
React SPA (Vite / Nginx)
   │  /api/v1/*  (no MSP keys, no peer URL)
   ▼
Django + DRF  ── SHA-256 hashes ──►  fabric-anchor  ──►  peer0 (AicteMSP)
   │                                      :8088              auditchannel / auditcc
   ▼
PostgreSQL
```

In development, Vite proxies `/api` to Django. In production, Nginx on the frontend image proxies `/api/` to the backend service.

Identity providers, Prometheus, and OpenSearch remain later-phase work. Fabric is optional: leave `FABRIC_ENABLED=false` until `./fabric/network.sh up`.

## 3. Repository map

```text
aicte-securedc/
├── backend/
│   ├── manage.py
│   ├── Dockerfile
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── development.txt
│   │   └── production.txt
│   ├── config/                    # Django project package (not a business app)
│   │   ├── settings/              # base / development / production
│   │   ├── urls.py                # admin + /api/
│   │   ├── api_urls.py            # /api/v1/ mount
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/
│       ├── core/                  # health, pagination, exception envelope
│       │   └── api/v1/
│       ├── accounts/              # placeholder — identity / RBAC
│       ├── inventory/             # placeholder — hardware assets
│       ├── compute/               # server inventory (CRUD)
│       ├── network/               # firewalls, rules, change-request approval
│       ├── licenses/              # placeholder — software licenses
│       ├── monitoring/            # placeholder — metrics / alerts
│       ├── audit/                 # append-only security audit log
│       ├── reports/               # placeholder — analytics
│       └── integrations/          # placeholder — ITSM / webhooks
├── frontend/
│   ├── Dockerfile                 # development target + production Nginx
│   ├── nginx.conf
│   └── src/
│       ├── api/                   # Axios instance and endpoint helpers
│       ├── components/            # shared UI (empty)
│       ├── context/               # global providers (empty)
│       ├── features/              # one folder per domain module later
│       ├── hooks/
│       ├── layouts/
│       ├── pages/                 # shell pages only
│       ├── routes/
│       └── utils/
├── fabric/
│   ├── crypto-config.yaml     # cryptogen orgs (test only)
│   ├── configtx.yaml          # AicteChannel, Raft orderer, AicteMSP
│   ├── docker-compose.yml     # orderer, peer, CLI, fabric-anchor
│   ├── network.sh             # generate / up / deployCC / down
│   ├── chaincode/auditcc/     # record* / getAuditHistory / verifyIntegrity
│   └── anchor/                # Fabric Gateway HTTP adapter
├── docker-compose.yml
├── .env.example
├── PROJECT_ARCHITECTURE.md
└── README.md
```

## 4. Backend design

### 4.1 Project vs apps

`config` is the Django project: settings, URL routing, WSGI/ASGI. It must not contain models.

`apps.*` are installable Django apps. Installed today: `apps.core`, `apps.accounts`, `apps.compute`, `apps.network`, `apps.monitoring`, `apps.audit`.

Future apps are directories only. When a phase lands:

1. Add `apps.py`, `models.py`, `services.py`, `api/v1/{serializers,views,urls}.py`.
2. Register the app in `config/settings/base.py` `INSTALLED_APPS`.
3. Include its URLs from `apps.core` or `config.api_urls` under `/api/v1/<resource>/`.

### 4.2 Settings split

| File | Role |
| --- | --- |
| `base.py` | Shared apps, middleware, DRF, Postgres, CORS |
| `development.py` | Debug, browsable API |
| `production.py` | TLS cookies, HSTS, JSON-only renderer |

`DJANGO_SETTINGS_MODULE` selects the module. Docker Compose defaults to development.

### 4.3 DRF conventions

- JSON in and out. Browsable API in development only.
- URLPath versioning: `/api/v1/`.
- Page-number pagination (`page`, `page_size`, max 100).
- Exception handler: `{ "success": false, "error": { "code", "message", "details" } }`.
- Permissions default to `IsAuthenticated`. Health, API root, register, login, and refresh are `AllowAny`.
- JWT access tokens (15 minutes, `Authorization: Bearer`) plus rotating refresh tokens (7 days) stored in an httpOnly `SameSite=Lax` cookie (`securedc_refresh`). Access tokens are kept in SPA memory, not `localStorage`.
- RBAC: `User` ⟷ `Role` ⟷ `Permission` (`resource:action`). Super Admin bypasses checks. DRF `HasPermission` enforces object APIs. Django `JWTAuthenticationMiddleware` + `AuthorizationMiddleware` sit on `/api/*`.

### 4.4 Database

PostgreSQL 16. Connection settings: `POSTGRES_*` env vars. `CONN_MAX_AGE=60`.

Phase 1 runs Django’s built-in migrations plus `accounts` (custom user, roles, permissions). `apps.core` has no domain models. `seed_rbac` creates the five system roles and bootstrap Super Admin.

### 4.5 API surface

| Method | Path | App | Notes |
| --- | --- | --- | --- |
| GET | `/api/v1/` | core | Catalog |
| GET | `/api/v1/health/` | core | Process + DB |
| POST | `/api/v1/auth/register/` | accounts | Public; no admin role |
| POST | `/api/v1/auth/login/` | accounts | Access JWT + refresh cookie |
| POST | `/api/v1/auth/refresh/` | accounts | Rotate refresh |
| POST | `/api/v1/auth/logout/` | accounts | Blacklist + clear cookie |
| GET/PATCH | `/api/v1/auth/me/` | accounts | Profile |
| POST | `/api/v1/auth/change-password/` | accounts | Re-hash; invalidate session |
| CRUD-ish | `/api/v1/users/` | accounts | `user:*` |
| CRUD-ish | `/api/v1/roles/` | accounts | `role:*` |
| CRUD-ish | `/api/v1/permissions/` | accounts | `permission:*` |
| GET | `/api/v1/dashboard/summary/` | monitoring | KPI cards |
| GET | `/api/v1/dashboard/charts/*` | monitoring | CPU, RAM, security events, alert trends |
| GET/POST | `/api/v1/servers/` | compute | List/search/filter (`server:read`) and add (`server:create`) |
| GET/PUT/PATCH/DELETE | `/api/v1/servers/{id}/` | compute | View (`server:read`), edit (`server:update`), delete (`server:delete`) |
| GET/POST | `/api/v1/firewalls/` | network | List (`firewall:read`) and add devices (`firewall:create`) |
| GET/PATCH | `/api/v1/firewalls/{id}/` | network | View / edit device (`firewall:update`) |
| GET | `/api/v1/firewall-rules/` | network | Live applied rules |
| GET/POST | `/api/v1/firewall-change-requests/` | network | Submit (`firewall:request`) and list |
| POST | `/api/v1/firewall-change-requests/{id}/approve/` | network | Security Admin (`firewall:approve`) |
| POST | `/api/v1/firewall-change-requests/{id}/reject/` | network | Security Admin (`firewall:reject`) |
| GET | `/api/v1/audit/summary/` | audit | KPI counts (`audit:read`) |
| GET | `/api/v1/audit/logs/` | audit | Search/filter (`audit:read`) |
| GET | `/api/v1/audit/logs/{id}/` | audit | Event details |
| GET | `/api/v1/audit/logs/{id}/verify/` | audit | Compare SHA-256 with Fabric (`verifyIntegrity`) |
| GET | `/api/v1/audit/logs/{id}/chain-history/` | audit | On-chain history (`getAuditHistory`) |
| GET | `/api/v1/blockchain/summary/` | audit | Verification KPIs |
| GET | `/api/v1/blockchain/transactions/` | audit | Tx IDs stored in PostgreSQL |
| POST | `/api/v1/blockchain/verify/` | audit | Integrity check API (`audit:verify`) |
| GET | `/api/v1/blockchain/alerts/` | audit | SECURITY ALERT list |

### 4.6 Roles (seeded)

| Slug | Name | Accounts access |
| --- | --- | --- |
| `super_admin` | Super Admin | All permissions |
| `security_admin` | Security Admin | Users, plus firewall approve/reject |
| `network_admin` | Network Admin | Firewalls, rule change requests |
| `server_admin` | Server Admin | Dashboard, servers, alerts |
| `auditor` | Auditor | Read-only including dashboard and audit logs |

Passwords: Argon2, min length 12, Django validators. Login: 5 attempts then 15-minute lockout; 5 req/min throttle. Users are disabled, never hard-deleted.

Firewall maker-checker: Network Admin submits rule add/edit/delete requests. Security Admin approves or rejects. The requester cannot review their own change. Applied rules change only after approval. Each decision is stored on `FirewallApprovalEvent`.

## 5. Frontend design

- Vite + React SPA. Tailwind for styling. React Router for routes. Axios for HTTP.
- `src/api/client.js` is the single Axios instance (`baseURL` = `VITE_API_BASE_URL`, credentials on).
- `src/features/` is reserved for domain UI. Do not put module screens in `pages/` except shell (home, 404).
- Layout: dark theme, sidebar + top bar (`AppLayout`). Login/register use `AuthLayout`.
- Dashboard: `src/features/monitoring` (KPI cards + Recharts). RBAC pages remain under `src/features/accounts`.
- Server management: `src/features/compute` (list, add, edit, details). Routes: `/servers`, `/servers/new`, `/servers/:id`, `/servers/:id/edit`.
- Firewall management: `src/features/network`. Routes: `/firewalls`, `/firewalls/:id`, `/firewall-approvals`.
- Audit: `src/features/audit`. Routes: `/audit`, `/audit/:id`. Append-only logs from `AuditLoggingMiddleware`. Detail page can verify the SHA-256 hash against Fabric.
- Blockchain verification: `src/features/blockchain`. Routes: `/blockchain`, `/blockchain/verify`, `/blockchain/transactions`, `/blockchain/alerts`.

## 6. Docker

Compose services: `db` (Postgres 16), `backend` (Django runserver + migrate), `frontend` (Vite dev server). Fabric is a **separate** Compose project (`fabric/docker-compose.yml`, network `fabric_test`) started by `./fabric/network.sh up`.

- Backend image: Python 3.12-slim, `psycopg2`, Gunicorn CMD for production use of the same Dockerfile.
- Frontend image: `development` target for Compose; `production` target builds static files into Nginx and reverse-proxies `/api/` to `backend:8000`.

Volumes: named `postgres_data`; backend and frontend source mounted in development for live reload.

## 7. Environment variables

| Variable | Used by | Purpose |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | backend | Signing |
| `DJANGO_DEBUG` | backend | Debug flag |
| `DJANGO_ALLOWED_HOSTS` | backend | Host header allowlist |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | backend | CSRF for SPA origins |
| `DJANGO_SETTINGS_MODULE` | backend | Settings module |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | backend, db | Database |
| `CORS_ALLOWED_ORIGINS` | backend | Browser origins |
| `JWT_SIGNING_KEY` | backend | JWT HMAC key (falls back to `DJANGO_SECRET_KEY`) |
| `JWT_REFRESH_COOKIE_SECURE` | backend | Secure flag on refresh cookie |
| `BOOTSTRAP_ADMIN_EMAIL` | backend | Seed Super Admin |
| `BOOTSTRAP_ADMIN_PASSWORD` | backend | Seed Super Admin password (min 12); unset skips seed |
| `VITE_API_BASE_URL` | frontend | Axios base path (`/api/v1`) |
| `VITE_PROXY_TARGET` | frontend (dev) | Vite proxy target for `/api` |
| `FABRIC_ENABLED` | backend | When true, hash critical audit rows and POST to the anchor |
| `FABRIC_ANCHOR_URL` | backend | Anchor base URL (`http://host.docker.internal:8088` in Compose) |

## 8. How later phases should land

| Phase theme | Django app | React folder | API prefix |
| --- | --- | --- | --- |
| Identity / RBAC | `apps.accounts` | `src/features/accounts` | `/api/v1/auth/`, `/users/`, `/roles/`, `/permissions/` | **done** |
| Cybersecurity dashboard | `apps.monitoring` | `src/features/monitoring` | `/api/v1/dashboard/` | **done** |
| Servers / LB | `apps.compute` | `src/features/compute` | `/api/v1/servers/` | **CRUD done** |
| Firewall / network | `apps.network` | `src/features/network` | `/api/v1/firewalls/` | **CRUD + approval done** |
| Licenses | `apps.licenses` | `src/features/licenses` | `/api/v1/licenses/` |
| Monitoring | `apps.monitoring` | `src/features/monitoring` | `/api/v1/alerts/`, `/metrics/` |
| Audit | `apps.audit` | `src/features/audit` | `/api/v1/audit/` | **done** |
| Blockchain anchoring | `apps.audit` + `fabric/` | audit detail verify | `/api/v1/audit/logs/{id}/verify/` | **done** |
| Blockchain verification | `apps.audit` | `src/features/blockchain` | `/api/v1/blockchain/` | **done** |
| Reports | `apps.reports` | `src/features/reports` | `/api/v1/reports/` |
| Integrations | `apps.integrations` | `src/features/integrations` | `/api/v1/webhooks/`, `/api-keys/` |

Rules:

- No cross-app model imports except via explicit service functions.
- Every mutating endpoint listed in the audit catalog writes an `AuditLog` row via middleware.
- Frontend never talks to Postgres or to a chain node; only `/api/v1/`. MSP private keys stay in `fabric/organizations` and are mounted read-only into `fabric-anchor`.

## 9. Security baseline (scaffold)

- Secrets only in environment / Compose `env_file`, not in images.
- Production settings enable secure cookies, HSTS, XSS/sniff/frame guards.
- CORS allowlist, not `*`.
- Passwords hashed with Argon2. JWT access in memory; refresh httpOnly, rotated and blacklisted on use/logout.
- Login lockout and throttling. Generic login errors. Super Admin assignment restricted. Last Super Admin cannot be stripped.
- CORS allowlist, not `*`.

Authentication and MFA remain later-phase work. Audit hashing is implemented: SHA-256 of canonical fields, submitted to Fabric when `FABRIC_ENABLED=true`.

## 10. Non-goals remaining

- Remaining DCIM modules (licenses, assets)
- Fabric CA / multi-orderer production topology (test network uses cryptogen + one Raft consenter)
- Kubernetes manifests
- Forced MFA / OIDC IdP
