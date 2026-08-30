export const AUDIT_ACTIONS = [
  { value: "login", label: "Login" },
  { value: "logout", label: "Logout" },
  { value: "server.create", label: "Server created" },
  { value: "server.update", label: "Server updated" },
  { value: "server.delete", label: "Server deleted" },
  { value: "firewall.create", label: "Firewall created" },
  { value: "firewall.update", label: "Firewall updated" },
  { value: "firewall.request", label: "Firewall change requested" },
  { value: "approval.approve", label: "Approved" },
  { value: "approval.reject", label: "Rejected" },
  { value: "user.create", label: "User created" },
  { value: "user.update", label: "User updated" },
  { value: "user.disable", label: "User disabled" },
  { value: "user.password_change", label: "Password changed" },
  { value: "role.create", label: "Role created" },
  { value: "role.update", label: "Role updated" },
  { value: "role.assign", label: "Roles assigned" },
];

export const RESOURCE_TYPES = [
  { value: "session", label: "Session" },
  { value: "user", label: "User" },
  { value: "role", label: "Role" },
  { value: "server", label: "Server" },
  { value: "firewall", label: "Firewall" },
  { value: "approval", label: "Approval" },
];

export function actionLabel(action) {
  return AUDIT_ACTIONS.find((item) => item.value === action)?.label || action;
}

export function resourceLabel(type) {
  return RESOURCE_TYPES.find((item) => item.value === type)?.label || type;
}
