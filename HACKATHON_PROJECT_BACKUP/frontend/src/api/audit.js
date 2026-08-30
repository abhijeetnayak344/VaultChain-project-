import api from "./client";

export function listAuditLogs(params) {
  return api.get("/audit/logs/", { params });
}

export function getAuditLog(id) {
  return api.get(`/audit/logs/${id}/`);
}

export function getAuditSummary() {
  return api.get("/audit/summary/");
}

export function verifyAuditLog(id) {
  return api.get(`/audit/logs/${id}/verify/`);
}

export function getAuditChainHistory(id) {
  return api.get(`/audit/logs/${id}/chain-history/`);
}
