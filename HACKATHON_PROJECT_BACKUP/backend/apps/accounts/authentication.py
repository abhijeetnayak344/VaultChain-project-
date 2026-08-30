from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication


class JWTAuthentication(SimpleJWTAuthentication):
    """DRF authentication: Authorization: Bearer <access>."""
