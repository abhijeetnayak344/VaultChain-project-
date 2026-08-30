import api from "./client";

export function listRoles() {
  return api.get("/roles/");
}

export function createRole(payload) {
  return api.post("/roles/", payload);
}

export function updateRole(id, payload) {
  return api.patch(`/roles/${id}/`, payload);
}

export function listPermissions() {
  return api.get("/permissions/");
}

export function createPermission(payload) {
  return api.post("/permissions/", payload);
}
