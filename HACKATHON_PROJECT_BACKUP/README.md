# AICTE SecureDC

Blockchain-enabled Cybersecurity & Data Center Management portal for the All India Council for Technical Education (AICTE).

This repository currently contains **Phase 1–8**: scaffold, identity/RBAC, cybersecurity dashboard, server management, firewall management, security audit logging, Hyperledger Fabric hash anchoring, and blockchain integrity verification.

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | Django, Django REST Framework |
| Database | PostgreSQL 16 |
| Infrastructure | Docker, Docker Compose |
| Ledger | Hyperledger Fabric 2.5 test network (audit hashes only) |

## Repository layout

```text
.
├── backend/                 Django project (config + apps)
├── frontend/                React + Vite SPA
├── fabric/                  Hyperledger Fabric 2.5 test network + chaincode
├── docker-compose.yml
├── .env.example
├── PROJECT_ARCHITECTURE.md
└── README.md
```

See [PROJECT_ARCHITECTURE.md](./PROJECT_ARCHITECTURE.md) for boundaries, API versioning, and how later phases plug in.

## Prerequisites

- Docker and Docker Compose
- Or locally: Python 3.12, Node.js 20, PostgreSQL 16

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API root | http://localhost:8000/api/v1/ |
| Health | http://localhost:8000/api/v1/health/ |
| Django admin | http://localhost:8000/admin/ |
| PostgreSQL | localhost:5432 |

The home page requires a signed-in session. Register a user or use the seeded Super Admin from `.env`.

Default Super Admin (development):

- Email: `dcim-admin@aicte.gov.in`
- Password: `ChangeMe!Admin12` (change immediately)

Compose runs `migrate` then `seed_rbac` on backend start. **If you already migrated before this phase, reset the database** (`docker compose down -v`) so the custom user model can install.

## Local development (without Docker)

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/development.txt
cp ../.env.example ../.env
# Set POSTGRES_HOST=localhost if Postgres runs on the host
python manage.py migrate
python manage.py seed_rbac
python manage.py seed_dashboard
python manage.py seed_audit
python manage.py seed_blockchain
python manage.py runserver 0.0.0.0:8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000` unless `VITE_PROXY_TARGET` is set.

## Environment

Copy `.env.example` to `.env`. All Django, Postgres, CORS, and Vite values are documented there. Do not commit real secrets.

## API

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/api/v1/` | public | API catalog |
| GET | `/api/v1/health/` | public | Liveness + PostgreSQL |
| POST | `/api/v1/auth/register/` | public | Register (no admin role) |
| POST | `/api/v1/auth/login/` | public | Login; access JWT + httpOnly refresh cookie |
| POST | `/api/v1/auth/refresh/` | cookie | Rotate refresh; new access token |
| POST | `/api/v1/auth/logout/` | JWT | Blacklist refresh; clear cookie |
| GET/PATCH | `/api/v1/auth/me/` | JWT | Profile |
| POST | `/api/v1/auth/change-password/` | JWT | Change password; invalidates session |
| GET/POST/PATCH | `/api/v1/users/` | `user:*` | User management |
| POST | `/api/v1/users/{id}/disable/` | `user:disable` | Soft-disable |
| POST | `/api/v1/users/{id}/roles/` | `role:assign` | Replace role set |
| GET/POST/PATCH | `/api/v1/roles/` | `role:*` | Role management |
| GET/POST/PATCH | `/api/v1/permissions/` | `permission:*` | Permission catalog |
| GET | `/api/v1/dashboard/summary/` | `dashboard:read` | KPI cards |
| GET | `/api/v1/dashboard/charts/cpu/` | `dashboard:read` | Hourly CPU average |
| GET | `/api/v1/dashboard/charts/ram/` | `dashboard:read` | Hourly RAM average |
| GET | `/api/v1/dashboard/charts/security-events/` | `dashboard:read` | Security event series |
| GET | `/api/v1/dashboard/charts/alerts/` | `dashboard:read` | Alert trends by severity |
| GET/POST | `/api/v1/servers/` | `server:read` / `server:create` | List (search/filter) and add |
| GET/PUT/PATCH/DELETE | `/api/v1/servers/{id}/` | `server:read` / `update` / `delete` | View, edit, delete |
| GET/POST | `/api/v1/firewalls/` | `firewall:read` / `firewall:create` | List and add firewall devices |
| GET/PATCH | `/api/v1/firewalls/{id}/` | `firewall:read` / `firewall:update` | View and edit device |
| GET | `/api/v1/firewall-rules/` | `firewall:read` | Live rules (`?firewall=`) |
| GET/POST | `/api/v1/firewall-change-requests/` | `firewall:read` / `firewall:request` | List and submit rule changes |
| POST | `/api/v1/firewall-change-requests/{id}/approve/` | `firewall:approve` | Apply pending change |
| POST | `/api/v1/firewall-change-requests/{id}/reject/` | `firewall:reject` | Reject pending change |
| GET | `/api/v1/audit/summary/` | `audit:read` | Audit KPI cards |
| GET | `/api/v1/audit/logs/` | `audit:read` | Search and filter audit events |
| GET | `/api/v1/audit/logs/{id}/` | `audit:read` | Audit event details |
| GET | `/api/v1/audit/logs/{id}/verify/` | `audit:read` | Compare current SHA-256 with on-chain hash |
| GET | `/api/v1/audit/logs/{id}/chain-history/` | `audit:read` | Ledger history for the event |
| GET | `/api/v1/blockchain/summary/` | `audit:read` | Blockchain verification KPIs |
| GET | `/api/v1/blockchain/transactions/` | `audit:read` | Transaction history (hashes + tx IDs) |
| GET | `/api/v1/blockchain/checks/` | `audit:read` | Integrity check history |
| POST | `/api/v1/blockchain/verify/` | `audit:verify` | Integrity check API (one event or scan) |
| GET | `/api/v1/blockchain/alerts/` | `audit:read` | Integrity security alerts |
| POST | `/api/v1/blockchain/alerts/{id}/acknowledge/` | `audit:alert` | Acknowledge alert |
| POST | `/api/v1/blockchain/alerts/{id}/resolve/` | `audit:alert` | Resolve alert |

Query params on `GET /api/v1/servers/`: `search`, `status`, `location`, `operating_system`, `page`, `page_size`.

SPA routes: `/servers` (list), `/servers/new` (add), `/servers/:id` (details), `/servers/:id/edit` (edit). Permissions: `server:read`, `server:create`, `server:update`, `server:delete`. Server Admin has full CRUD; Security Admin and Auditor are read-only.

Firewall SPA: `/firewalls`, `/firewalls/new`, `/firewalls/:id` (rules), `/firewalls/:id/edit`, `/firewall-approvals`. Network Admin requests rule changes; Security Admin approves or rejects. Requesters cannot review their own changes.

Audit SPA: `/audit`, `/audit/:id`. Blockchain SPA: `/blockchain`, `/blockchain/verify`, `/blockchain/transactions`, `/blockchain/alerts`. `audit:read` is granted to Super Admin, Security Admin, and Auditor. Re-run `seed_rbac` after pulling this phase so `audit:verify` and `audit:alert` exist.

## Hyperledger Fabric (audit hashes)

The app stack runs without Fabric (`FABRIC_ENABLED=false`). To anchor critical audit hashes:

```bash
chmod +x fabric/network.sh
./fabric/network.sh up
```

Then set `FABRIC_ENABLED=true` in `.env` and restart the backend. Django stores a SHA-256 of stable audit fields and submits it through `fabric-anchor` (`localhost:8088`) to chaincode `auditcc` on channel `auditchannel`. The SPA never holds MSP keys and never talks to a peer.

Integrity check: **current data hash vs blockchain hash**. Match → **VERIFIED**. Mismatch → **SECURITY ALERT** on `/blockchain/alerts`.

Guides: [docs/FABRIC_SETUP.md](./docs/FABRIC_SETUP.md), [docs/FABRIC_INTEGRATION.md](./docs/FABRIC_INTEGRATION.md).
