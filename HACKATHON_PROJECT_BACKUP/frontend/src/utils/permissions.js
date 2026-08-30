export function hasPermission(user, codename) {
  if (!user) return false;
  if (user.is_super_admin) return true;
  return Array.isArray(user.permissions) && user.permissions.includes(codename);
}

export function hasRole(user, slug) {
  if (!user) return false;
  if (user.is_super_admin && slug === "super_admin") return true;
  return Array.isArray(user.roles) && user.roles.some((role) => role.slug === slug);
}
