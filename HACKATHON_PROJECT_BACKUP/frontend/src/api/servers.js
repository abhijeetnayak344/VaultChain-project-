import api from "./client";

export function listServers(params) {
  return api.get("/servers/", { params: { page_size: 100, ...params } });
}

export function getServer(id) {
  return api.get(`/servers/${id}/`);
}

export function createServer(payload) {
  return api.post("/servers/", payload);
}

export function updateServer(id, payload) {
  return api.patch(`/servers/${id}/`, payload);
}

export function deleteServer(id) {
  return api.delete(`/servers/${id}/`);
}
