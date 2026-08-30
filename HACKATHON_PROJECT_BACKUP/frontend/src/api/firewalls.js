import api from "./client";

export function listFirewalls(params) {
  return api.get("/firewalls/", { params: { page_size: 100, ...params } });
}

export function getFirewall(id) {
  return api.get(`/firewalls/${id}/`);
}

export function createFirewall(payload) {
  return api.post("/firewalls/", payload);
}

export function updateFirewall(id, payload) {
  return api.patch(`/firewalls/${id}/`, payload);
}

export function listFirewallRules(params) {
  return api.get("/firewall-rules/", { params: { page_size: 100, ...params } });
}

export function listChangeRequests(params) {
  return api.get("/firewall-change-requests/", { params: { page_size: 100, ...params } });
}

export function getChangeRequest(id) {
  return api.get(`/firewall-change-requests/${id}/`);
}

export function createChangeRequest(payload) {
  return api.post("/firewall-change-requests/", payload);
}

export function approveChangeRequest(id, payload = {}) {
  return api.post(`/firewall-change-requests/${id}/approve/`, payload);
}

export function rejectChangeRequest(id, payload = {}) {
  return api.post(`/firewall-change-requests/${id}/reject/`, payload);
}
