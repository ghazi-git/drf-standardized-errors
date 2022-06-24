SECRET_KEY = "some_secret_key"

USE_TZ = True

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "drf_standardized_errors",
)

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

MIDDLEWARE_CLASSES = ("django.middleware.common.CommonMiddleware",)

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

ROOT_URLCONF = "tests.urls"

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
