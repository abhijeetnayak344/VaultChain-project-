from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.constants import SUPER_ADMIN
from apps.accounts.models import Permission, Role, User


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ("id", "resource", "action", "codename", "description", "created_at")
        read_only_fields = ("id", "codename", "created_at")


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source="permissions",
    )

    class Meta:
        model = Role
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_system",
            "permissions",
            "permission_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "is_system", "created_at", "updated_at")

    def validate_slug(self, value):
        return value.strip().lower().replace(" ", "_")

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance and instance.is_system and "slug" in attrs and attrs["slug"] != instance.slug:
            raise serializers.ValidationError({"slug": "System role slugs cannot be changed."})
        return attrs


class RoleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "slug")


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSummarySerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    is_super_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "is_active",
            "is_super_admin",
            "roles",
            "permissions",
            "date_joined",
            "last_login",
        )
        read_only_fields = fields

    def get_permissions(self, obj):
        return obj.permission_codenames()

    def get_is_super_admin(self, obj):
        return obj.is_platform_super_admin()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("email", "full_name", "password")

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_email(self, value):
        return value.lower().strip()


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name",)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        if attrs["current_password"] == attrs["new_password"]:
            raise serializers.ValidationError({"new_password": "New password must be different."})
        return attrs


class AdminUserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=12)
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        many=True,
        required=False,
        source="roles",
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "password", "is_active", "role_ids")

    def validate_email(self, value):
        return value.lower().strip()

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_roles(self, roles):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if any(role.slug == SUPER_ADMIN for role in roles):
            if not user or not user.is_authenticated or not user.is_platform_super_admin():
                raise serializers.ValidationError("Only Super Admin can assign the Super Admin role.")
        return roles

    def create(self, validated_data):
        roles = validated_data.pop("roles", [])
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError({"password": "Password is required when creating a user."})
        user = User.objects.create_user(password=password, **validated_data)
        if roles:
            user.roles.set(roles)
        return user

    def update(self, instance, validated_data):
        roles = validated_data.pop("roles", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            instance.roles.set(roles)
        return instance
