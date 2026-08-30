#!/usr/bin/env bash
# Bring up the AICTE SecureDC Hyperledger Fabric 2.5 test network.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

FABRIC_VERSION="${FABRIC_VERSION:-2.5}"
CHANNEL_NAME="${CHANNEL_NAME:-auditchannel}"
CC_NAME="${CC_NAME:-auditcc}"
CC_VERSION="${CC_VERSION:-1.0}"
CC_SEQUENCE="${CC_SEQUENCE:-1}"
TOOLS_IMAGE="hyperledger/fabric-tools:${FABRIC_VERSION}"
COMPOSE=(docker compose -f docker-compose.yml)

ORDERER_CA="crypto/ordererOrganizations/aicte.gov.in/orderers/orderer.aicte.gov.in/tls/ca.crt"
PEER_TLS="crypto/peerOrganizations/securedc.aicte.gov.in/peers/peer0.securedc.aicte.gov.in/tls/ca.crt"
OSN_CERT="crypto/ordererOrganizations/aicte.gov.in/orderers/orderer.aicte.gov.in/tls/server.crt"
OSN_KEY="crypto/ordererOrganizations/aicte.gov.in/orderers/orderer.aicte.gov.in/tls/server.key"

function generate() {
  echo "==> Generating crypto material (cryptogen — test only)"
  rm -rf organizations channel-artifacts
  mkdir -p channel-artifacts
  docker run --rm -v "$ROOT":/work -w /work "$TOOLS_IMAGE" \
    cryptogen generate --config=/work/crypto-config.yaml --output=/work/organizations

  echo "==> Generating channel genesis block"
  docker run --rm -v "$ROOT":/work -w /work \
    -e FABRIC_CFG_PATH=/work \
    "$TOOLS_IMAGE" \
    configtxgen -profile AicteChannel -outputBlock ./channel-artifacts/${CHANNEL_NAME}.block -channelID "$CHANNEL_NAME"
}

function up() {
  if [[ ! -f "organizations/peerOrganizations/securedc.aicte.gov.in/peers/peer0.securedc.aicte.gov.in/msp/signcerts/peer0.securedc.aicte.gov.in-cert.pem" ]]; then
    generate
  fi
  echo "==> Starting orderer and peer"
  "${COMPOSE[@]}" up -d orderer.aicte.gov.in peer0.securedc.aicte.gov.in cli
  echo "==> Waiting for orderer admin (9443)"
  for _ in $(seq 1 30); do
    if docker exec fabric-cli osnadmin channel list \
      -o orderer.aicte.gov.in:9443 \
      --ca-file "/opt/gopath/src/github.com/hyperledger/fabric/peer/${ORDERER_CA}" \
      --client-cert "/opt/gopath/src/github.com/hyperledger/fabric/peer/${OSN_CERT}" \
      --client-key "/opt/gopath/src/github.com/hyperledger/fabric/peer/${OSN_KEY}" \
      >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
  createChannel
  deployCC
  echo "==> Starting Fabric Gateway anchor"
  "${COMPOSE[@]}" up -d --build fabric-anchor
  echo "==> Fabric test network is ready (channel=${CHANNEL_NAME}, chaincode=${CC_NAME})"
}

function createChannel() {
  echo "==> Orderer joining channel ${CHANNEL_NAME}"
  docker exec fabric-cli osnadmin channel join \
    --channelID "$CHANNEL_NAME" \
    --config-block "/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts/${CHANNEL_NAME}.block" \
    -o orderer.aicte.gov.in:9443 \
    --ca-file "/opt/gopath/src/github.com/hyperledger/fabric/peer/${ORDERER_CA}" \
    --client-cert "/opt/gopath/src/github.com/hyperledger/fabric/peer/${OSN_CERT}" \
    --client-key "/opt/gopath/src/github.com/hyperledger/fabric/peer/${OSN_KEY}" \
    || echo "==> Orderer already participates in ${CHANNEL_NAME} (continuing)"

  echo "==> Peer joining channel ${CHANNEL_NAME}"
  docker exec fabric-cli peer channel join \
    -b "/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts/${CHANNEL_NAME}.block" \
    || echo "==> Peer already joined ${CHANNEL_NAME} (continuing)"
}

function deployCC() {
  if docker exec fabric-cli peer lifecycle chaincode querycommitted \
    --channelID "$CHANNEL_NAME" --name "$CC_NAME" >/dev/null 2>&1; then
    echo "==> Chaincode ${CC_NAME} already committed on ${CHANNEL_NAME}"
    return
  fi
  echo "==> Installing Node chaincode dependencies"
  docker run --rm -v "$ROOT/chaincode/auditcc":/cc -w /cc node:20-alpine npm install --omit=dev
  echo "==> Packaging chaincode ${CC_NAME}"
  docker exec fabric-cli peer lifecycle chaincode package "${CC_NAME}.tar.gz" \
    --path /opt/gopath/src/github.com/chaincode/auditcc \
    --lang node \
    --label "${CC_NAME}_${CC_VERSION}"

  echo "==> Installing chaincode on peer"
  docker exec fabric-cli peer lifecycle chaincode install "${CC_NAME}.tar.gz"

  PACKAGE_ID="$(docker exec fabric-cli peer lifecycle chaincode queryinstalled \
    | sed -n 's/^Package ID: \(.*\), Label: '"${CC_NAME}_${CC_VERSION}"'.*/\1/p' | tail -1)"
  echo "==> Package ID: ${PACKAGE_ID}"

  docker exec fabric-cli peer lifecycle chaincode approveformyorg \
    -o orderer.aicte.gov.in:7050 \
    --ordererTLSHostnameOverride orderer.aicte.gov.in \
    --channelID "$CHANNEL_NAME" \
    --name "$CC_NAME" \
    --version "$CC_VERSION" \
    --package-id "$PACKAGE_ID" \
    --sequence "$CC_SEQUENCE" \
    --tls \
    --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/${ORDERER_CA}

  docker exec fabric-cli peer lifecycle chaincode commit \
    -o orderer.aicte.gov.in:7050 \
    --ordererTLSHostnameOverride orderer.aicte.gov.in \
    --channelID "$CHANNEL_NAME" \
    --name "$CC_NAME" \
    --version "$CC_VERSION" \
    --sequence "$CC_SEQUENCE" \
    --tls \
    --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/${ORDERER_CA} \
    --peerAddresses peer0.securedc.aicte.gov.in:7051 \
    --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/${PEER_TLS}

  docker exec fabric-cli peer chaincode query \
    -C "$CHANNEL_NAME" \
    -n "$CC_NAME" \
    -c '{"Args":["getAuditHistory","healthcheck"]}' || true
}

function down() {
  "${COMPOSE[@]}" down --volumes --remove-orphans || true
  ids="$(docker ps -aq --filter name=dev-peer0.securedc 2>/dev/null || true)"
  if [[ -n "${ids}" ]]; then
    docker rm -f ${ids} 2>/dev/null || true
  fi
  echo "==> Network stopped. Crypto material kept. Use './network.sh clean' to delete it."
}

function clean() {
  down
  rm -rf organizations channel-artifacts
  echo "==> Crypto and channel artifacts removed."
}

case "${1:-}" in
  generate) generate ;;
  up) up ;;
  down) down ;;
  clean) clean ;;
  createChannel) createChannel ;;
  deployCC) deployCC ;;
  *)
    echo "Usage: $0 {generate|up|down|clean|createChannel|deployCC}"
    exit 1
    ;;
esac
