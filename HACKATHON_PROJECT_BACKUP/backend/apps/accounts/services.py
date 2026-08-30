from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    roles = list(user.roles.values_list("slug", flat=True))
    refresh["email"] = user.email
    refresh["roles"] = roles
    access = refresh.access_token
    access["email"] = user.email
    access["roles"] = roles
    return str(access), str(refresh)


def set_refresh_cookie(response, refresh_token):
    max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        path=settings.JWT_REFRESH_COOKIE_PATH,
    )
    return response


def clear_refresh_cookie(response):
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )
    return response


def get_refresh_token_from_request(request):
    cookie = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
    if cookie:
        return cookie
    if hasattr(request, "data"):
        return request.data.get("refresh")
    return None


def register_failed_login(user):
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= settings.LOGIN_FAILURE_LIMIT:
        user.locked_until = timezone.now() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        user.failed_login_attempts = 0
    user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])


def reset_failed_login(user):
    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])
