"""In-memory SQLite settings for Django tests."""

from .base import *  # noqa: F403

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
FABRIC_ENABLED = False
FABRIC_ANCHOR_URL = "http://127.0.0.1:8088"
