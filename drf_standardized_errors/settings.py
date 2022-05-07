from typing import Dict

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from rest_framework.settings import APISettings


class PackageSettings(APISettings):
    """
    APISettings is quite the nice class for managing settings, just wish that
    DRF changes its stance on keeping APISettings internal.
    """

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "DRF_STANDARDIZED_ERRORS", {})
        return self._user_settings

    def __check_user_settings(self, user_settings):
        return user_settings


DEFAULTS: Dict = {
    "EXCEPTION_HANDLER_CLASS": "drf_standardized_errors.handler.ExceptionHandler",
    "EXCEPTION_FORMATTER_CLASS": "drf_standardized_errors.formatter.ExceptionFormatter",
    "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": False,
    "NESTED_FIELD_SEPARATOR": ".",
}

IMPORT_STRINGS = ("EXCEPTION_FORMATTER_CLASS", "EXCEPTION_HANDLER_CLASS")

package_settings = PackageSettings(None, DEFAULTS, IMPORT_STRINGS)


@receiver(setting_changed)
def reload_package_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "DRF_STANDARDIZED_ERRORS":
        package_settings.reload()
