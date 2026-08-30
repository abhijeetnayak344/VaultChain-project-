from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.authentication import JWTAuthentication


class JWTAuthenticationMiddleware:
    """Authentication middleware: attach request.user from Bearer access token on /api/*."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.authenticator = JWTAuthentication()

    def __call__(self, request):
        if request.path.startswith("/api/"):
            try:
                result = self.authenticator.authenticate(request)
            except AuthenticationFailed:
                result = None
            if result is not None:
                request.user, request.auth = result
        return self.get_response(request)


class AuthorizationMiddleware:
    """
    Authorization middleware: marks public API routes.
    Permission checks are enforced by DRF HasPermission so clients always get
    the standard JSON error envelope.
    """

    PUBLIC_PREFIXES = (
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/admin",
        "/static",
        "/media",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.is_public_api = self._is_public(request.path)
        return self.get_response(request)

    def _is_public(self, path):
        if path.rstrip("/") in {"/api/v1", "/api"}:
            return True
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)
