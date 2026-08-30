# Hyperledger Fabric Integration

How AICTE SecureDC stores **critical audit event hashes** on Fabric without putting chain keys or raw logs in the React SPA.

## Trust model

1. Django writes the append-only Postgres `audit_log` row (source of operational truth).
2. A canonical JSON subset is hashed with SHA-256 (`apps.audit.blockchain.event_hash`).
3. If `FABRIC_ENABLED=true`, the backend POSTs **only the hash and identifiers** to `fabric-anchor`.
4. `fabric-anchor` uses the official **Fabric Gateway** (`@hyperledger/fabric-gateway`) with the Aicte org user identity to submit/evaluate chaincode.
5. The SPA calls `/api/v1/audit/logs/{id}/verify/` — it never talks to a peer.

Passwords and tokens are already redacted in audit `details` by `AuditLoggingMiddleware`. Those details are **not** part of the on-chain hash (stable identity fields only).

## Canonical hash payload

```json
{
  "action": "server.update",
  "actor_email": "dcim-admin@aicte.gov.in",
  "ip_address": "10.20.1.40",
  "log_id": "…uuid…",
  "resource_id": "…",
  "resource_type": "server",
  "timestamp": "2026-08-13T06:30:00+00:00"
}
```

Keys are sorted; separators are compact. Changing any of these fields after anchoring makes `verifyIntegrity` fail.

## Chaincode mapping

| Audit `resource_type` | Chaincode function | Arguments |
| --- | --- | --- |
| `server` | `recordServerChange` | `eventId, hash, serverId, timestamp` |
| `firewall`, `approval` | `recordFirewallChange` | `changeId, hash, firewallId, timestamp` |
| `user`, `role`, `session` | `recordAuditEvent` | `eventId, hash, resourceType, timestamp` |

Reads:

- `GET /api/v1/audit/logs/{id}/verify/` → persist check; **VERIFIED** or **SECURITY ALERT**
- `POST /api/v1/blockchain/verify/` → integrity check API (one id or recent scan)
- `GET /api/v1/blockchain/summary/` → dashboard KPIs
- `GET /api/v1/blockchain/transactions/` → PostgreSQL copy of chain tx IDs
- `GET /api/v1/blockchain/alerts/` → mismatch alerts
- `GET /api/v1/audit/logs/{id}/chain-history/` → `getAuditHistory`

## Verification workflow

1. A critical action writes an `AuditLog` row.
2. Django computes SHA-256 of the canonical fields and stores `integrity_hash`.
3. If Fabric is enabled, `fabric-anchor` submits the hash; `chain_tx_id` is saved on the same row.
4. Integrity check compares **current data hash** vs **blockchain hash**.
5. Match → `verification_status=verified` (**VERIFIED**). Mismatch → `verification_status=alert` and an `IntegrityAlert` (**SECURITY ALERT**).

Django modules:

| Module | Role |
| --- | --- |
| `apps.audit.blockchain` | Hash, schedule, fetch chain integrity, history |
| `apps.audit.verification` | Classify match/mismatch, persist checks, open alerts |
| `apps.audit.services.record_event` | Calls `schedule_anchor` after insert |
| `AuditLog.integrity_hash` / `chain_tx_id` / `chain_status` / `verification_status` | Local copy of anchor and verify outcome |

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `FABRIC_ENABLED` | `false` | Skip anchoring when the test network is down |
| `FABRIC_ANCHOR_URL` | `http://127.0.0.1:8088` | Anchor base URL. Compose uses `http://host.docker.internal:8088` |

Anchoring is asynchronous (daemon thread). A Fabric outage **does not** fail login or CRUD. `chain_status` becomes `pending` → `anchored` or `failed`.

## Anchor HTTP API (internal)

`fabric-anchor` is not a public API. It is bound for local Docker/host use.

| Method | Path | Body |
| --- | --- | --- |
| GET | `/health` | — |
| POST | `/api/v1/anchor` | `{ "function": "recordAuditEvent", "args": ["…"] }` |
| POST | `/api/v1/verify` | `{ "eventId": "…", "hash": "…" }` |
| GET | `/api/v1/history/:id` | — |

Allowed submit functions are allow-listed in `fabric/anchor/src/index.js`.

## Failure behaviour

- Fabric down: row stays in Postgres, `chain_status=failed`, UI shows skipped/failed.
- Duplicate event id on chain: chaincode rejects; Django records `failed`.
- SPA cannot reach the peer even if a user opens DevTools — there is no Fabric URL in Vite env.

See [FABRIC_SETUP.md](./FABRIC_SETUP.md) to start the test network.
