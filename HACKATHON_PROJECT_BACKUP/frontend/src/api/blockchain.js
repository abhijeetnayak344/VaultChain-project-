import api from "./client";

export function getBlockchainSummary() {
  return api.get("/blockchain/summary/");
}

export function listBlockchainTransactions(params) {
  return api.get("/blockchain/transactions/", { params });
}

export function listIntegrityChecks(params) {
  return api.get("/blockchain/checks/", { params });
}

export function runIntegrityCheck(body) {
  return api.post("/blockchain/verify/", body);
}

export function listIntegrityAlerts(params) {
  return api.get("/blockchain/alerts/", { params });
}

export function acknowledgeIntegrityAlert(id) {
  return api.post(`/blockchain/alerts/${id}/acknowledge/`);
}

export function resolveIntegrityAlert(id) {
  return api.post(`/blockchain/alerts/${id}/resolve/`);
}
