from unittest.mock import MagicMock

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.signals import got_request_exception
from django.http import Http404
from rest_framework.exceptions import (
    APIException,
    ErrorDetail,
    PermissionDenied,
    ValidationError,
)

from drf_standardized_errors.handler import exception_handler


@pytest.fixture
def validation_error():
    return ValidationError(
        {"name": [ErrorDetail("This field is required.", code="required")]}
    )


def test_validation_error(validation_error, exception_context):
    response = exception_handler(validation_error, exception_context)
    assert response.status_code == 400
    assert response.data["type"] == "validation_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "required"
    assert error["detail"] == "This field is required."
    assert error["attr"] == "name"


@pytest.fixture
def permission_denied_error():
    return PermissionDenied()


def test_permission_denied_error(permission_denied_error, exception_context):
    response = exception_handler(permission_denied_error, exception_context)
    assert response.status_code == 403
    assert response.data["type"] == "client_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "permission_denied"
    assert error["detail"] == "You do not have permission to perform this action."
    assert error["attr"] is None


@pytest.fixture
def server_error():
    return APIException()


def test_server_error(server_error, exception_context):
    response = exception_handler(server_error, exception_context)
    assert response.status_code == 500
    assert response.data["type"] == "server_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "error"
    assert error["detail"] == "A server error occurred."
    assert error["attr"] is None


@pytest.fixture
def service_unavailable_error():
    return ServiceUnavailable()


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = "Service temporarily unavailable, try again later."
    default_code = "service_unavailable"


def test_custom_exception(service_unavailable_error, exception_context):
    response = exception_handler(service_unavailable_error, exception_context)
    assert response.status_code == 503
    assert response.data["type"] == "server_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "service_unavailable"
    assert error["detail"] == "Service temporarily unavailable, try again later."
    assert error["attr"] is None


@pytest.fixture
def unhandled_exception():
    return Exception()


def test_unhandled_exception(settings, unhandled_exception, exception_context):
    settings.DEBUG = True
    response = exception_handler(unhandled_exception, exception_context)
    assert response is None


def test_got_request_exception_signal_sent(server_error, exception_context):
    # register a signal handler
    mock = MagicMock()
    got_request_exception.connect(mock)

    exception_handler(server_error, exception_context)
    assert mock.called


def test_got_request_exception_signal_not_sent(validation_error, exception_context):
    # register a signal handler
    mock = MagicMock()
    got_request_exception.connect(mock)

    exception_handler(validation_error, exception_context)
    assert mock.called is False


@pytest.fixture
def django_permission_denied():
    return DjangoPermissionDenied()


def test_django_permission_denied_conversion(
    django_permission_denied, exception_context
):
    response = exception_handler(django_permission_denied, exception_context)
    assert response.status_code == 403
    assert response.data["type"] == "client_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "permission_denied"


@pytest.fixture
def http404_error():
    return Http404()


def test_django_http404_conversion(http404_error, exception_context):
    response = exception_handler(http404_error, exception_context)
    assert response.status_code == 404
    assert response.data["type"] == "client_error"
    assert len(response.data["errors"]) == 1
    error = response.data["errors"][0]
    assert error["code"] == "not_found"


def test_auth_header_is_set(api_client):
    response = api_client.get("/auth-error/")
    assert response.status_code == 401
    auth_header = response.headers.get("WWW-Authenticate")
    assert auth_header == 'Basic realm="api"'


def test_retry_after_header_is_set(api_client):
    response = api_client.get("/rate-limit-error/")
    assert response.status_code == 429
    retry_after_header = response.headers.get("Retry-After")
    assert retry_after_header == "600"
