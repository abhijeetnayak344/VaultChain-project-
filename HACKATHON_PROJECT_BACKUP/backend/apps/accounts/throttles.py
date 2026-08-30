from rest_framework.throttling import ScopedRateThrottle


class AuthBurstThrottle(ScopedRateThrottle):
    scope = "auth"
