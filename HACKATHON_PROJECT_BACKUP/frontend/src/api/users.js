import api from "./client";

export function listUsers(params) {
  return api.get("/users/", { params });
}

export function createUser(payload) {
  return api.post("/users/", payload);
}

export function updateUser(id, payload) {
  return api.patch(`/users/${id}/`, payload);
}

export function disableUser(id) {
  return api.post(`/users/${id}/disable/`);
}

export function assignUserRoles(id, roleIds) {
  return api.post(`/users/${id}/roles/`, { role_ids: roleIds });
}
