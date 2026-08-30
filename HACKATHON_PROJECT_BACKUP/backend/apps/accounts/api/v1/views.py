from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.api.serializers import (
    AdminUserWriteSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    PermissionSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    RoleSerializer,
    UserSerializer,
)
from apps.accounts.constants import SUPER_ADMIN
from apps.accounts.models import Permission, Role, User
from apps.accounts.permissions import IsSuperAdmin, require_permission
from apps.accounts.services import (
    clear_refresh_cookie,
    get_refresh_token_from_request,
    issue_tokens_for_user,
    register_failed_login,
    reset_failed_login,
    set_refresh_cookie,
)


def _auth_response(user, status_code=status.HTTP_200_OK):
    access, refresh = issue_tokens_for_user(user)
    response = Response(
        {"access": access, "user": UserSerializer(user).data},
        status=status_code,
    )
    set_refresh_cookie(response, refresh)
    return response


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return _auth_response(user, status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        try:
            user = User.objects.prefetch_related("roles__permissions").get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid email or password.")

        if user.is_locked():
            raise AuthenticationFailed("Account is temporarily locked. Try again later.")
        if not user.is_active:
            raise AuthenticationFailed("Account is disabled.")
        if not user.check_password(password):
            register_failed_login(user)
            raise AuthenticationFailed("Invalid email or password.")

        reset_failed_login(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login", "updated_at"])
        return _auth_response(user)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        raw = get_refresh_token_from_request(request)
        if not raw:
            raise AuthenticationFailed("Refresh token is missing.")
        try:
            token = RefreshToken(raw)
            user_id = token.payload.get("user_id")
            user = User.objects.prefetch_related("roles__permissions").get(pk=user_id)
            token.blacklist()
        except (TokenError, User.DoesNotExist):
            response = Response(
                {
                    "success": False,
                    "error": {"code": 401, "message": "Session expired.", "details": None},
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_refresh_cookie(response)
            return response

        if not user.is_active or user.is_locked():
            raise AuthenticationFailed("Account is not allowed to refresh a session.")
        return _auth_response(user)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = get_refresh_token_from_request(request)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        response = Response({"detail": "Logged out."})
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.prefetch_related("roles__permissions").get(pk=request.user.pk)
        return Response(UserSerializer(user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user = User.objects.prefetch_related("roles__permissions").get(pk=request.user.pk)
        return Response(UserSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.password_changed_at = timezone.now()
        user.save(update_fields=["password", "password_changed_at", "updated_at"])
        response = Response({"detail": "Password updated. Please sign in again."})
        raw = get_refresh_token_from_request(request)
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        clear_refresh_cookie(response)
        return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("roles__permissions").all()
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require_permission("user:read")()]
        if self.action == "create":
            return [IsAuthenticated(), require_permission("user:create")()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), require_permission("user:update")()]
        if self.action == "disable":
            return [IsAuthenticated(), require_permission("user:disable")()]
        if self.action == "assign_roles":
            return [IsAuthenticated(), require_permission("role:assign")()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update", "update"):
            return AdminUserWriteSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        if user.is_platform_super_admin() and not self.request.user.is_platform_super_admin():
            raise PermissionDenied("Only Super Admin can create another Super Admin.")

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.is_platform_super_admin() and not self.request.user.is_platform_super_admin():
            raise PermissionDenied("Only Super Admin can modify a Super Admin.")
        serializer.save()

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError("You cannot disable your own account.")
        if user.is_platform_super_admin() and not request.user.is_platform_super_admin():
            raise PermissionDenied("Only Super Admin can disable a Super Admin.")
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="roles")
    def assign_roles(self, request, pk=None):
        user = self.get_object()
        role_ids = request.data.get("role_ids", [])
        roles = list(Role.objects.filter(pk__in=role_ids))
        if any(role.slug == SUPER_ADMIN for role in roles) and not request.user.is_platform_super_admin():
            raise PermissionDenied("Only Super Admin can assign the Super Admin role.")
        if user.is_platform_super_admin() and not any(role.slug == SUPER_ADMIN for role in roles):
            remaining = User.objects.filter(roles__slug=SUPER_ADMIN, is_active=True).exclude(pk=user.pk).count()
            if remaining < 1:
                raise ValidationError("Cannot remove the last Super Admin.")
        user.roles.set(roles)
        user = User.objects.prefetch_related("roles__permissions").get(pk=user.pk)
        return Response(UserSerializer(user).data)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.prefetch_related("permissions").all()
    serializer_class = RoleSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require_permission("role:read")()]
        if self.action == "create":
            return [IsAuthenticated(), require_permission("role:create")()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), require_permission("role:update")()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.is_system and serializer.validated_data.get("slug") not in (None, instance.slug):
            raise ValidationError("System role slugs cannot be changed.")
        serializer.save()


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), require_permission("permission:read")()]
        if self.action == "create":
            return [IsAuthenticated(), IsSuperAdmin()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), require_permission("permission:update")()]
        return [IsAuthenticated()]
