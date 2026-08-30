# auditcc

Node.js chaincode for AICTE SecureDC. Stores **SHA-256 hashes** of critical audit events, not raw payloads.

| Function | Args | Writes |
| --- | --- | --- |
| `recordAuditEvent` | `eventId, hash, resourceType, timestamp` | `EVENT:{eventId}` |
| `recordFirewallChange` | `changeId, hash, firewallId, timestamp` | same, `kind=firewall` |
| `recordServerChange` | `eventId, hash, serverId, timestamp` | same, `kind=server` |
| `getAuditHistory` | `id` | read current + `getHistoryForKey`, or resource matches |
| `verifyIntegrity` | `eventId, hash` | compare on-chain hash |

Duplicate `eventId` values are rejected. Deployed by `./fabric/network.sh up` as `auditcc` on channel `auditchannel`.
