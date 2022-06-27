from django.db import IntegrityError
from rest_framework.exceptions import APIException

from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.handler import ExceptionHandler, exception_handler
from drf_standardized_errors.types import ErrorResponse


def test_custom_exception_handler_class(settings, api_client):
    settings.DRF_STANDARDIZED_ERRORS = {
        "EXCEPTION_HANDLER_CLASS": "tests.test_settings.CustomExceptionHandler"
    }
    response = api_client.post("/integrity-error/")
    assert response.status_code == 409
    assert response.data["type"] == "client_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "conflict"
    assert error["detail"] == "Concurrent update prevented."
    assert error["attr"] is None


class CustomExceptionHandler(ExceptionHandler):
    def convert_known_exceptions(self, exc: Exception) -> Exception:
        if isinstance(exc, IntegrityError):
            return ConcurrentUpdateError(str(exc))
        else:
            return super().convert_known_exceptions(exc)


class ConcurrentUpdateError(APIException):
    status_code = 409
    default_code = "conflict"


def test_custom_exception_formatter_class(settings, api_client):
    settings.DRF_STANDARDIZED_ERRORS = {
        "EXCEPTION_FORMATTER_CLASS": "tests.test_settings.CustomExceptionFormatter"
    }
    response = api_client.get("/error/")
    assert response.status_code == 500
    assert response.data["type"] == "server_error"
    assert response.data["code"] == "error"
    assert response.data["message"] == "Internal server error."
    assert response.data["field_name"] is None


class CustomExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        """return one error at a time and change error response key names"""
        error = error_response.errors[0]
        return {
            "type": error_response.type,
            "code": error.code,
            "message": error.detail,
            "field_name": error.attr,
        }


def test_enable_in_debug_for_unhandled_exception_is_false(
    settings, exc, exception_context
):
    settings.DEBUG = True
    settings.DRF_STANDARDIZED_ERRORS = {
        "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": False
    }
    response = exception_handler(exc, exception_context)
    assert response is None


def test_enable_in_debug_for_unhandled_exception_is_true(
    settings, exc, exception_context
):
    settings.DEBUG = True
    settings.DRF_STANDARDIZED_ERRORS = {
        "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True
    }
    response = exception_handler(exc, exception_context)
    assert response is not None
    assert response.status_code == 500
    assert response.data["type"] == "server_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "error"
    assert error["detail"] == "Internal server error."
    assert error["attr"] is None


def test_nested_field_separator(settings, api_client):
    settings.DRF_STANDARDIZED_ERRORS = {"NESTED_FIELD_SEPARATOR": "__"}
    address = {
        "street_address": "123 Main street",
        "city": "Floral Park",
        "state": "NY",
        "zipcode": "11001",
    }
    response = api_client.post("/order-error/", data={"shipping_address": address})
    assert response.status_code == 400
    assert response.data["type"] == "validation_error"
    error = response.data["errors"][0]
    assert error["code"] == "unsupported"
    assert error["attr"] == "shipping_address__state"
