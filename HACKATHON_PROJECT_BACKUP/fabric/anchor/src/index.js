'use strict';

const fs = require('fs');
const path = require('path');
const grpc = require('@grpc/grpc-js');
const { connect, hash, signers } = require('@hyperledger/fabric-gateway');
const crypto = require('crypto');
const express = require('express');

const PEER_ENDPOINT = process.env.FABRIC_PEER_ENDPOINT || 'peer0.securedc.aicte.gov.in:7051';
const PEER_HOST_OVERRIDE = process.env.FABRIC_PEER_HOST_OVERRIDE || 'peer0.securedc.aicte.gov.in';
const MSP_ID = process.env.FABRIC_MSP_ID || 'AicteMSP';
const CHANNEL = process.env.FABRIC_CHANNEL || 'auditchannel';
const CHAINCODE = process.env.FABRIC_CHAINCODE || 'auditcc';
const CRYPTO_PATH = process.env.FABRIC_CRYPTO_PATH || '/crypto';
const PORT = Number(process.env.FABRIC_ANCHOR_PORT || 8088);

const orgPath = path.join(CRYPTO_PATH, 'peerOrganizations', 'securedc.aicte.gov.in');
const tlsCertPath = path.join(
  orgPath,
  'peers',
  'peer0.securedc.aicte.gov.in',
  'tls',
  'ca.crt'
);
const certDir = path.join(orgPath, 'users', 'User1@securedc.aicte.gov.in', 'msp', 'signcerts');
const keyDir = path.join(orgPath, 'users', 'User1@securedc.aicte.gov.in', 'msp', 'keystore');

function firstFile(dir) {
  const files = fs.readdirSync(dir).filter((name) => !name.startsWith('.'));
  if (!files.length) {
    throw new Error(`No files in ${dir}`);
  }
  return path.join(dir, files[0]);
}

function utf8(bytes) {
  return Buffer.from(bytes).toString('utf8');
}

let contract;

async function openGateway() {
  const tlsRoot = fs.readFileSync(tlsCertPath);
  const certPem = fs.readFileSync(firstFile(certDir));
  const keyPem = fs.readFileSync(firstFile(keyDir));
  const ssl = grpc.credentials.createSsl(tlsRoot);
  const client = new grpc.Client(PEER_ENDPOINT, ssl, {
    'grpc.ssl_target_name_override': PEER_HOST_OVERRIDE,
  });
  const gateway = connect({
    client,
    identity: { mspId: MSP_ID, credentials: certPem },
    signer: signers.newPrivateKeySigner(crypto.createPrivateKey(keyPem)),
    hash: hash.sha256,
  });
  contract = gateway.getNetwork(CHANNEL).getContract(CHAINCODE);
  console.log(`Connected to ${PEER_ENDPOINT} channel=${CHANNEL} cc=${CHAINCODE}`);
}

function parseResult(bytes) {
  if (!bytes || !bytes.length) {
    return {};
  }
  const text = utf8(bytes);
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

const app = express();
app.use(express.json({ limit: '32kb' }));

app.get('/health', (_req, res) => {
  res.json({ status: contract ? 'ok' : 'starting', service: 'fabric-anchor' });
});

function requireContract(res) {
  if (!contract) {
    res.status(503).json({ error: 'Fabric Gateway is not connected yet' });
    return false;
  }
  return true;
}

app.post('/api/v1/anchor', async (req, res) => {
  try {
    if (!requireContract(res)) {
      return;
    }
    const { function: fn, args } = req.body || {};
    const allowed = new Set([
      'recordAuditEvent',
      'recordFirewallChange',
      'recordServerChange',
    ]);
    if (!allowed.has(fn)) {
      res.status(400).json({ error: 'Unsupported chaincode function' });
      return;
    }
    const payload = Array.isArray(args) ? args.map((value) => String(value ?? '')) : [];
    const result = await contract.submitTransaction(fn, ...payload);
    res.json({ ok: true, function: fn, result: parseResult(result) });
  } catch (err) {
    res.status(502).json({ error: err.message || String(err) });
  }
});

app.post('/api/v1/verify', async (req, res) => {
  try {
    if (!requireContract(res)) {
      return;
    }
    const { eventId, hash: eventHash } = req.body || {};
    const result = await contract.evaluateTransaction('verifyIntegrity', String(eventId || ''), String(eventHash || ''));
    res.json(parseResult(result));
  } catch (err) {
    res.status(502).json({ error: err.message || String(err) });
  }
});

app.get('/api/v1/history/:id', async (req, res) => {
  try {
    if (!requireContract(res)) {
      return;
    }
    const result = await contract.evaluateTransaction('getAuditHistory', req.params.id);
    res.json(parseResult(result));
  } catch (err) {
    res.status(502).json({ error: err.message || String(err) });
  }
});

async function main() {
  for (let attempt = 1; attempt <= 30; attempt += 1) {
    try {
      await openGateway();
      break;
    } catch (err) {
      console.error(`Gateway connect attempt ${attempt}: ${err.message}`);
      if (attempt === 30) {
        throw err;
      }
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }
  }
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`fabric-anchor listening on ${PORT}`);
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
