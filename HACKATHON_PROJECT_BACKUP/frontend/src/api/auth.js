import api from "./client";

export function login(payload) {
  return api.post("/auth/login/", payload);
}

export function register(payload) {
  return api.post("/auth/register/", payload);
}

export function refreshSession() {
  return api.post("/auth/refresh/");
}

export function logout() {
  return api.post("/auth/logout/");
}

export function getMe() {
  return api.get("/auth/me/");
}

export function updateMe(payload) {
  return api.patch("/auth/me/", payload);
}

export function changePassword(payload) {
  return api.post("/auth/change-password/", payload);
}
