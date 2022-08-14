from typing import Dict

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from rest_framework.settings import import_from_string, perform_import


class PackageSettings:
    """
    Copy of DRF APISettings class with support for importing settings that
    are dicts with value as a string representing the path to the class
    to be imported.
    """

    setting_name = "DRF_STANDARDIZED_ERRORS"

    def __init__(self, defaults=None, import_strings=None):
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, self.setting_name, {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            if isinstance(val, dict):
                val = {
                    status_code: import_from_string(error_schema, attr)
                    for status_code, error_schema in val.items()
                }
            else:
                val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


DEFAULTS: Dict = {
    "EXCEPTION_HANDLER_CLASS": "drf_standardized_errors.handler.ExceptionHandler",
    "EXCEPTION_FORMATTER_CLASS": "drf_standardized_errors.formatter.ExceptionFormatter",
    "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": False,
    "NESTED_FIELD_SEPARATOR": ".",
    "ALLOWED_ERROR_STATUS_CODES": [
        "400",
        "401",
        "403",
        "404",
        "405",
        "406",
        "415",
        "429",
        "500",
    ],
    # A mapping used to override the default serializers used to describe
    # the error response. The key is the status code and the value is a string
    # that represents the path to the serializer class that describes the
    # error response.
    "ERROR_SCHEMAS": None,
    # When there is a validation error in list serializers, the "attr" returned
    # will be sth like "0.email", "1.email", "2.email", ... So, to describe
    # the error codes linked to the same field in a list serializer, the field
    # will appear in the schema with the name "INDEX.email"
    "LIST_INDEX_IN_API_SCHEMA": "INDEX",
    # When there is a validation error in a DictField with the name "extra_data",
    # the "attr" returned will be sth like "extra_data.<key1>", "extra_data.<key2>",
    # "extra_data.<key3>", ... Since the keys of a DictField are not predetermined,
    # this setting is used as a common name to be used in the API schema. So, the
    # corresponding "attr" value for the previous example will be "extra_data.KEY"
    "DICT_KEY_IN_API_SCHEMA": "KEY",
    # should be unique to error components since it is used to identify error
    # components generated dynamically to exclude them from being processed by
    # the postprocessing hook. This avoids raising warnings for "code" and "attr"
    # which can have the same choices across multiple serializers.
    "ERROR_COMPONENT_NAME_SUFFIX": "ErrorComponent",
}

IMPORT_STRINGS = (
    "EXCEPTION_FORMATTER_CLASS",
    "EXCEPTION_HANDLER_CLASS",
    "ERROR_SCHEMAS",
)

package_settings = PackageSettings(DEFAULTS, IMPORT_STRINGS)


@receiver(setting_changed)
def reload_package_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == package_settings.setting_name:
        package_settings.reload()
