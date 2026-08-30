# AICTE DCIM Portal — Phase 1 Foundation Design

Date: 2026-08-13
Status: Draft pending user review
Scope: Phase 1 only (scaffold, identity, RBAC/ABAC, audit). Later DCIM modules are out of scope except reserved permission strings and placeholder UI cards.

## 1. Problem and goal

AICTE manages infrastructure with fragmented tools, weak license tracking, and no centralized access control. The portal is a single org-scoped, role-based web application for HQ, regional offices, and affiliated institutes.

Phase 1 delivers the backbone every later module depends on:

- Monorepo scaffold (API, web, shared, Docker, Kubernetes placeholders)
- OIDC SSO via self-hosted Keycloak (BFF sessions in Redis)
- Multi-org hierarchy with ABAC (`org_id` + ancestors/descendants)
- Eight operational roles and a frozen permission catalog
- Central append-only, hash-chained audit log in PostgreSQL

## 2. Architecture

BFF monorepo (pnpm workspaces):

| Path | Role |
|------|------|
| `apps/api` | NestJS REST (`/api/v1/*`), Prisma → PostgreSQL, Redis sessions, IdP-agnostic OIDC client |
| `apps/web` | Vite + React + TypeScript + Tailwind. No tokens in JS. Cookie session only. |
| `packages/shared` | Permission catalog, role names, org types, audit actions, error codes. Imported by API and web so UI gates and guards cannot drift. |
| `infra/docker` | Compose: Postgres 16, Redis 7, Keycloak 26, API, web, nginx (same-origin) |
| `infra/k8s` | Placeholder Deployments/Services. Not a working cluster in Phase 1. |
| `infra/keycloak` | Versioned realm `aicte-dcim` and confidential client `dcim-web` (API-only) |

Request path: browser → nginx `/` (web) and `/api` (API) → Postgres / Redis / Keycloak.

The API is a BFF: it holds OIDC tokens in Redis, sets an httpOnly `Secure` `SameSite=Lax` host-only cookie, and never exposes access or refresh tokens to the browser.

NestJS modules in Phase 1: `Health`, `Auth`, `Orgs`, `Users`, `Rbac`, `Audit`.

Cross-cutting: `SessionGuard` (cookie → Redis, token refresh), `RbacGuard` (`@RequirePermission` + org subtree), `AuditInterceptor`.

Web Phase 1 pages: Login (redirect), Dashboard (placeholder cards for later modules), Organizations (tree), Users, Role assignments, Audit log (filters + before/after diff). Components: `PermissionGate`, `OrgSwitcher`, `AuditDiff`.

No server, firewall, license, or asset tables in this phase.

## 3. Organization model

Multi-org hierarchy: HQ → regional office → affiliated institute → optional `unit`.

Storage: adjacency list plus closure table.

- `organizations.parent_id` is the editable tree.
- `org_closure(ancestor_id, descendant_id, depth)` is written in the same transaction as org create/move/delete. Every org has a self-row at depth 0.

ABAC “in my subtree?” is one indexed lookup:

```
WHERE descendant_id = resource.org_id AND ancestor_id = session.org_id
```

Org moves rewrite only the affected closure rows. No Postgres `ltree`.

Org types in `packages/shared`: `hq | regional | institute | unit`.

## 4. Identity

Keycloak 26 in Docker Compose. Realm and clients versioned in-repo. Local `docker compose up` is a full login path. No cloud IdP in Phase 1.

NestJS OIDC client stays IdP-agnostic (issuer, client id/secret, redirect URI from env) so Azure AD or NIC ePramaan can replace Keycloak without rewriting RBAC.

- Flow: Authorization Code + PKCE.
- Client `dcim-web` is confidential and used only by the API.
- TOTP MFA is available on the realm, optional per user in Phase 1 (not globally forced).
- Keycloak groups may mirror org codes as hints. **Postgres is the authorization source of truth.**

### 4.1 Login

1. Protected route → web calls `GET /api/v1/auth/me`.
2. `401` → browser goes to `GET /api/v1/auth/login`.
3. API starts Authorization Code + PKCE, redirects to Keycloak.
4. User authenticates (optional TOTP).
5. `GET /api/v1/auth/callback` exchanges the code, upserts the local user by OIDC `sub` + email (re-created Keycloak users do not duplicate local rows), creates Redis session, sets cookie, redirects to `/`.

### 4.2 Session

Redis session payload: `{ userId, orgId, roles, accessToken, refreshToken, expiresAt }`.

Cookie: httpOnly, Secure, SameSite=Lax, host-only. Idle 8 hours, absolute 12 hours. Sliding idle TTL on activity.

Keycloak access token TTL: 5 minutes. Refresh token TTL: 30 minutes, rotated on use.

On each API call, if the access token is expired the API refreshes from Redis, stores the new pair, slides idle TTL.

**Session fully dead path:** if the refresh token is expired, reuse is detected, or Keycloak rotation fails, the API deletes the Redis session, clears the cookie, and returns `401` with `error.code = SESSION_EXPIRED`. The web client then sends the user through `GET /auth/login` again.

### 4.3 Logout

`POST /auth/logout`:

1. Revoke the Keycloak refresh token.
2. Call Keycloak end-session (back-channel) so the SSO session dies.
3. Delete the Redis session.
4. Clear the cookie.
5. Audit `session.logout`.

If Keycloak is unreachable, the local session is still destroyed and the IdP failure is audited. A live API session is never left because IdP logout failed.

### 4.4 Org switch

`POST /auth/switch-org` succeeds only when the user has at least one `user_org_roles` row for the target org. It then updates Redis `orgId` and audits `session.switch_org`. Any other org id (unknown, or no grant) returns `404 NOT_FOUND` — no existence leak, no 403 on this path.

### 4.5 Bootstrap

Keycloak realm import includes a dev user `dcim-admin`. API seed creates the HQ org, maps that user by `sub`+email, assigns `super_admin` at HQ.

Production: if `BOOTSTRAP_ADMIN_PASSWORD` is unset, the seed refuses to create the default user. The documented temp password exists only for local Compose.

## 5. RBAC / ABAC

Eight seeded roles: `super_admin`, `org_admin`, `network_admin`, `security_admin`, `license_manager`, `asset_manager`, `operator`, `auditor`.

Permissions are `resource:action` strings in `packages/shared`. A user holds roles via `user_org_roles` (role is always scoped to an org).

Effective access:

1. Session org + role grants → permission set.
2. Resource `org_id` must be a descendant of `session.org_id` in `org_closure` (self included).
3. Sole exception: `super_admin` with `*:*` bypasses the subtree check.

**403 vs 404:**

- `403 FORBIDDEN` — authenticated, resource is in the caller’s subtree, permission grant missing (e.g. operator `user:update`).
- `404 NOT_FOUND` — resource missing **or** outside `org_closure` (exists or not). Same code; no existence leak. Sibling-org access is always 404.

Firewall maker-checker: `network_admin` can create/read/update/delete firewall objects; only `security_admin` has `firewall:approve`. The proposer cannot approve their own change. Enforcement of “same user cannot approve their own change” is application logic in the firewall module (later phase); Phase 1 only seeds the split grants.

### 5.1 Permission catalog

Phase 1 resources (enforced now): `org`, `user`, `role`, `session`, `audit`.

Reserved resources (seeded now, unused until later modules): `server`, `firewall`, `network_device`, `load_balancer`, `license`, `asset`, `alert`, `report`, `api_key`, `integration`.

Actions: `create`, `read`, `update`, `disable`, `assign`, `revoke`, `export`, `approve`, `provision`, `renew`, `ack`, `schedule`, `manage`.

`user:delete` does not exist. Offboarding is `user:disable` only (`disabled_at` set, login blocked, row retained so `audit_events.actor_user_id` stays valid). A future `user:erase` (PII scrub, UUID kept) is `super_admin`-only and is not a Phase 1 action.

Grant matrix (`*` = all actions defined for that resource; `—` = none). All grants except `super_admin` `*:*` are org-scoped via `org_closure`.

| Resource | super_admin | org_admin | network_admin | security_admin | license_manager | asset_manager | operator | auditor |
|----------|-------------|-----------|---------------|----------------|-----------------|---------------|----------|---------|
| org | * | create, read, update, delete | read | read | read | read | read | read |
| user | * (create, read, update, disable) | create, read, update, disable | read | read | read | read | read | read |
| role | * | read, assign | read | read | read | read | read | read |
| session | * | read, revoke | read | read, revoke | — | — | — | read |
| audit | * | read | read | read, export | read | read | read | read, export |
| server | * | read | * | read | — | read | read | read |
| firewall | * | read | create, read, update, delete | * (incl. approve) | — | — | read | read |
| network_device | * | read | * | read | — | — | read | read |
| load_balancer | * | read | * | read | — | — | read | read |
| license | * | read | — | read | * (incl. renew) | read | read | read |
| asset | * | read | — | read | read | * | read | read |
| alert | * | read | read, ack | read, ack | — | — | read, ack | read |
| report | * | read, create, schedule | read | read | read | read | read | read |
| api_key | * | create, read, revoke | — | read | — | — | — | read |
| integration | * | read, manage | — | read | — | — | — | read |

`org_admin` `api_key` create/revoke and `integration` manage are intentional subtree self-serve for later ITSM/webhook work. An institute admin cannot mint keys that reach outside their closure.

`org:create` always inserts a child whose `parent_id` is in the caller’s closure (typically the session org). The HQ row is created only by seed, not by a normal create call.

`packages/shared` exports this matrix. Seed scripts and `RbacGuard` tests import it; they must not hard-code a second copy.

## 6. Data model (PostgreSQL)

Prisma: snake_case columns, camelCase client. `deleted_at` only on `organizations` (and not on users — users use `disabled_at`). Audit rows are never soft-deleted.

Tenancy: `org_id` foreign keys plus `RbacGuard`. No Postgres RLS in Phase 1.

### 6.1 Core tables

**organizations** — `id`, `parent_id` (nullable, HQ has null), `name`, `code` (unique), `type`, `created_at`, `updated_at`, `deleted_at`.

**org_closure** — `ancestor_id`, `descendant_id`, `depth`. Primary key `(ancestor_id, descendant_id)`. Indexes on both directions.

**users** — `id`, `idp_sub` (unique), `email` (unique), `display_name`, `disabled_at` (nullable), `created_at`, `updated_at`. No hard delete.

**roles** — `id`, `name` (unique, matches catalog), `description`.

**permissions** — `id`, `resource`, `action`, unique `(resource, action)`.

**role_permissions** — `role_id`, `permission_id`.

**user_org_roles** — `user_id`, `org_id`, `role_id`, unique `(user_id, org_id, role_id)`.

**audit_events** — append-only (see §7).

Application DB role has no UPDATE or DELETE on `audit_events`. A trigger rejects those operations.

## 7. Audit

PostgreSQL is the Phase 1 source of truth. OpenSearch is deferred.

Every mutating request and every auth event (login, logout, switch-org, denied authorization) writes one row.

Columns: `id`, `occurred_at`, `actor_user_id` (nullable for system), `actor_org_id`, `session_id`, `request_id`, `ip`, `user_agent`, `action`, `resource_type`, `resource_id`, `org_id` (resource org), `outcome` (`success` \| `denied` \| `failure`), `http_method`, `http_path`, `http_status`, `before_json`, `after_json`, `metadata`, `prev_hash`, `hash`.

`hash` is SHA-256 of a canonical payload plus `prev_hash`. Phase 1 runs a single API replica so the chain is linear. Multi-replica chaining is out of scope.

Denied permission checks audit `outcome: denied`. They do not skip the log.

`GET /audit` is cursor-paginated, requires `audit:read`, and is itself org-scoped (events whose `org_id` is in the caller’s closure, plus the caller’s own auth events). `audit:export` is required to download.

## 8. HTTP API conventions

Base path: `/api/v1`.

Success: resource JSON. Lists: `{ data, nextCursor? }`.

Failure envelope:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action.",
    "details": null,
    "requestId": "uuid"
  }
}
```

`requestId` is generated per request and echoed on `X-Request-Id` so clients, logs, and `audit_events.request_id` join. `message` is UI-safe. Prisma and Keycloak internals never appear in `message` or `details`.

| HTTP | code | when |
|------|------|------|
| 400 | `VALIDATION_ERROR` | Bad body/query; `details` is a field list |
| 401 | `UNAUTHENTICATED` | No or invalid cookie |
| 401 | `SESSION_EXPIRED` | Refresh dead path; Redis and cookie already cleared |
| 403 | `FORBIDDEN` | In-subtree, missing permission grant |
| 404 | `NOT_FOUND` | Missing or outside subtree |
| 409 | `CONFLICT` | Org cycle, duplicate role assignment, `idp_sub` clash |
| 429 | `RATE_LIMITED` | `/auth/*` only in Phase 1 |
| 502 | `IDP_UNAVAILABLE` | Keycloak down on login/logout/refresh; logout still destroys local session |
| 503 | `NOT_READY` | `/ready` when Postgres or Redis is down |

Idempotent GETs on a dead session return `401 SESSION_EXPIRED`, never a half-hydrated user.

Same-origin BFF: nginx serves web at `/` and API at `/api`. Dev: Vite proxies `/api` to the API. No CORS credentials to arbitrary origins. CSRF defense in Phase 1 is same-origin + `SameSite=Lax`, not a second token.

Health: `GET /health` liveness (process up). `GET /ready` checks Postgres and Redis.

Auth routes: `GET /auth/login`, `GET /auth/callback`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/switch-org`.

## 9. Frontend

TanStack Query for server state. Auth/session via `GET /auth/me` (cookie). `PermissionGate` hides nav and actions using the same catalog as the API. Org switcher lists only orgs where `GET /auth/me` reports a role grant.

No DCIM entity screens in Phase 1.

## 10. Docker and config

Compose services: `postgres`, `redis`, `keycloak`, `api`, `web`, `nginx`.

Secrets and passwords via env files, not committed. Dev realm import is versioned; production realm import must not include `dcim-admin` unless `BOOTSTRAP_ADMIN_PASSWORD` is set through a secret.

Kubernetes manifests under `infra/k8s` are structural placeholders (Deployment/Service per app) so later phases do not invent a layout.

## 11. Testing

Phase 1 is not done until these exist.

**Unit**

- `RbacGuard` table-driven cases imported from `packages/shared`: including absence of `user:delete`, firewall maker-checker (`network_admin` has no `approve`), `org_admin` `api_key:create` inside vs outside subtree, operator `user:update` → 403, sibling org → 404.
- `org_closure` create, move, delete.
- Audit hash: canonical payload + `prev_hash` → `hash`. UPDATE/DELETE on `audit_events` rejected.

**Integration**

- Testcontainers Postgres + Redis. Keycloak mocked at the OIDC client (CI does not boot a realm).
- Login callback upsert-by-`sub`.
- Refresh expiry → `SESSION_EXPIRED`.
- Logout deletes Redis even if IdP logout fails.
- Org switch refused without a role grant.

**E2E (Playwright, Compose profile)**

- Login as `dcim-admin`.
- Create a regional org, assign `org_admin`, switch org.
- Sibling-org access returns 404.
- Denied `user:update` writes `audit.outcome = denied`.

## 12. Out of scope for Phase 1

Server/firewall/load-balancer/license/asset CRUD and schemas. Prometheus, Grafana, OpenSearch. Real webhook/ITSM adapters. Postgres RLS. Forced MFA for all users. `user:erase`. Working Kubernetes cluster. Next.js, Casbin, JWT-in-browser.

## 13. Decisions log

| Decision | Choice |
|----------|--------|
| Tenancy | Multi-org hierarchy (HQ → regional → institute) |
| IdP | Keycloak 26 in Compose; NestJS IdP-agnostic |
| Layout | pnpm BFF monorepo, Redis httpOnly session |
| Org tree | Adjacency list + closure table |
| Audit store | PostgreSQL only; OpenSearch later |
| Roles | Eight operational roles |
| User offboarding | `disable` only; no `user:delete` |
| API keys | `org_admin` create/read/revoke in subtree |
| Out-of-subtree | Always 404, never 403 |
| Permission miss in-subtree | 403 |
| Logout | Local session destroy + Keycloak end-session |
| Refresh failure | Clear session, `SESSION_EXPIRED` |
| CSRF | Same-origin proxy + SameSite=Lax |
| Frontend data | TanStack Query |
| RLS | Not in Phase 1 |
