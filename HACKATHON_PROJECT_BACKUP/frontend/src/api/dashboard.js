import api from "./client";

export function getDashboardSummary() {
  return api.get("/dashboard/summary/");
}

export function getCpuChart(hours = 24) {
  return api.get("/dashboard/charts/cpu/", { params: { hours } });
}

export function getRamChart(hours = 24) {
  return api.get("/dashboard/charts/ram/", { params: { hours } });
}

export function getSecurityEventsChart(days = 7) {
  return api.get("/dashboard/charts/security-events/", { params: { days } });
}

export function getAlertTrends(days = 14) {
  return api.get("/dashboard/charts/alerts/", { params: { days } });
}
