# Hyperledger Fabric Test Network — Setup Guide

AICTE SecureDC anchors **SHA-256 hashes of critical audit events** on a Hyperledger Fabric 2.5 test network. Raw audit payloads, passwords, and private keys never go to the browser or onto the ledger.

This network is for **local development and demonstration**. `cryptogen` is not a production CA. Production must use Fabric CA, multiple orderers, and proper secret storage.

## Topology

| Node | MSP | Endpoint |
| --- | --- | --- |
| Orderer (etcd/Raft, single consenter) | `OrdererMSP` | `orderer.aicte.gov.in:7050` (admin `9443`) |
| Peer | `AicteMSP` (org `Aicte` / `securedc.aicte.gov.in`) | `peer0.securedc.aicte.gov.in:7051` |
| Channel | `auditchannel` | application channel genesis (no system channel) |
| Chaincode | `auditcc` | Node.js contract API |
| Anchor adapter | `fabric-anchor` | `http://localhost:8088` (Fabric Gateway) |

```text
SecureDC SPA  →  Django /api/v1  →  fabric-anchor  →  peer Gateway  →  auditcc
                     (hashes only)     (private key)      (gRPC/TLS)
```

## Prerequisites

- Docker and Docker Compose v2
- ~4 GB RAM for peer + orderer + chaincode container
- Linux/macOS (Docker Desktop is supported)

You do **not** need Fabric binaries on the host. `network.sh` runs `cryptogen` and `configtxgen` inside `hyperledger/fabric-tools:2.5`.

## Bring the network up

From the repository root:

```bash
chmod +x fabric/network.sh
./fabric/network.sh up
```

What this does:

1. Generates org crypto with `cryptogen` (`fabric/crypto-config.yaml`)
2. Builds the `auditchannel` genesis block (`fabric/configtx.yaml` profile `AicteChannel`)
3. Starts orderer + peer + CLI (`fabric/docker-compose.yml`)
4. Joins the orderer via the channel participation API (`osnadmin`)
5. Joins `peer0` to `auditchannel`
6. Packages, installs, approves, and commits `auditcc`
7. Starts `fabric-anchor` on port **8088**

Health check:

```bash
curl -s http://localhost:8088/health
```

## Point SecureDC at Fabric

In `.env`:

```bash
FABRIC_ENABLED=true
FABRIC_ANCHOR_URL=http://host.docker.internal:8088
```

If Django runs on the host instead of Compose:

```bash
FABRIC_ANCHOR_URL=http://127.0.0.1:8088
```

Then restart the backend (`docker compose up -d backend` or `runserver`). New audit events get a SHA-256 `integrity_hash` and are submitted to chaincode. Open an audit detail page and use **Verify on Fabric**.

## Chaincode functions

| Function | Purpose |
| --- | --- |
| `recordAuditEvent` | Anchor a generic audit hash |
| `recordFirewallChange` | Anchor a firewall / approval change hash |
| `recordServerChange` | Anchor a server change hash |
| `getAuditHistory` | Current record + ledger history |
| `verifyIntegrity` | Compare a local hash with the on-chain hash |

## Common commands

```bash
./fabric/network.sh down     # stop containers, keep crypto
./fabric/network.sh clean    # stop and delete crypto + genesis
./fabric/network.sh generate # crypto + genesis only
```

## Files

| Path | Role |
| --- | --- |
| `fabric/crypto-config.yaml` | Test orgs, peer, orderer (cryptogen) |
| `fabric/configtx.yaml` | Channel, Raft consenter, MSPs, capabilities V2_0 |
| `fabric/docker-compose.yml` | Orderer, peer, CLI, anchor |
| `fabric/chaincode/auditcc/` | Chaincode |
| `fabric/anchor/` | Fabric Gateway HTTP adapter |
| `fabric/network.sh` | Generate / up / deploy / down |

Generated material (`organizations/`, `channel-artifacts/`) is gitignored. Never commit MSP private keys.

## Production notes (not this test network)

- Replace `cryptogen` with Fabric CA and separate TLS CAs
- Run at least three Raft consenters
- Store peer/orderer identities in a secret manager, not bind mounts of PEM files into the SPA image
- Pin image digests; do not expose peer 7051 or orderer 7050 to the public internet
- Keep the SPA on `/api/v1` only — it must never hold an MSP key
