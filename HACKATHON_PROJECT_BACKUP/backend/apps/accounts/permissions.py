from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """Authorization: authenticated user must hold a permission codename (or Super Admin)."""

    message = "You do not have permission to perform this action."

    def __init__(self, codename):
        self.codename = codename

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_perm_codename(self.codename)


def require_permission(codename):
    class BoundHasPermission(HasPermission):
        def __init__(self):
            super().__init__(codename)

    BoundHasPermission.__name__ = f"HasPermission_{codename.replace(':', '_')}"
    return BoundHasPermission


class IsSuperAdmin(BasePermission):
    message = "Super Admin access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_platform_super_admin())
