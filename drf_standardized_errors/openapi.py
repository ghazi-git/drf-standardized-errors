from typing import List

from drf_spectacular.openapi import AutoSchema as BaseAutoSchema
from drf_spectacular.utils import OpenApiExample, PolymorphicProxySerializer
from inflection import camelize
from rest_framework import exceptions
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.parsers import FileUploadParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.status import is_client_error
from rest_framework.versioning import (
    AcceptHeaderVersioning,
    HostNameVersioning,
    NamespaceVersioning,
    QueryParameterVersioning,
    URLPathVersioning,
)

from .handler import exception_handler as standardized_errors_handler
from .openapi_serializers import (
    ErrorResponse401Serializer,
    ErrorResponse403Serializer,
    ErrorResponse404Serializer,
    ErrorResponse406Serializer,
    ErrorResponse415Serializer,
    ErrorResponse429Serializer,
    ErrorResponse500Serializer,
    ParseErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)
from .settings import package_settings


class AutoSchema(BaseAutoSchema):
    def _get_response_bodies(self):
        responses = super()._get_response_bodies()
        error_responses = {}

        status_codes = self._get_allowed_error_status_codes()
        for status_code in status_codes:
            if self._should_add_error_response(responses, status_code):
                serializer = self._get_error_response_serializer(status_code)
                if not serializer:
                    continue
                error_responses[status_code] = self._get_response_for_code(
                    serializer, status_code
                )

        return {**error_responses, **responses}

    def _get_allowed_error_status_codes(self) -> List[str]:
        allowed_status_codes = package_settings.ALLOWED_ERROR_STATUS_CODES or []
        return [str(status_code) for status_code in allowed_status_codes]

    def _should_add_error_response(self, responses: dict, status_code: str) -> bool:
        if (
            self.view.get_exception_handler() is not standardized_errors_handler
            or status_code in responses
        ):
            # this means that the exception handler has been overridden for this view
            # or the error response has already been added via extend_schema, so we
            # should not override that
            return False

        if status_code == "400":
            return (
                self._should_add_parse_error_response()
                or self._should_add_validation_error_response()
            )
        elif status_code == "401":
            return self._should_add_http401_error_response()
        elif status_code == "403":
            return self._should_add_http403_error_response()
        elif status_code == "404":
            return self._should_add_http404_error_response()
        elif status_code == "406":
            return self._should_add_http406_error_response()
        elif status_code == "415":
            return self._should_add_http415_error_response()
        elif status_code == "429":
            return self._should_add_http429_error_response()
        elif status_code == "500":
            return self._should_add_http500_error_response()
        else:
            # user might add extra status codes and their serializers, so we
            # should always add corresponding error responses
            return True

    def _should_add_parse_error_response(self) -> bool:
        parsers = self.view.get_parsers()
        parsers_that_raise_parse_errors = (
            JSONParser,
            MultiPartParser,
            FileUploadParser,
        )
        return any(
            isinstance(parser, parsers_that_raise_parse_errors) for parser in parsers
        )

    def _should_add_validation_error_response(self) -> bool:
        """
        add a validation error response when unsafe methods have a request body
        or when a list view implements filtering with django-filters.
        todo add a way to disable adding the 400 validation response on an
         operation-basis. This is because "serializer.is_valid" has the option
         of not raising an exception. At the very least, add docs to demo what
         to override to accomplish that (maybe sth like
         isinstance(self.view, SomeViewSet) and checking self.method)
        """
        has_request_body = self.method in ("PUT", "PATCH", "POST") and bool(
            self.get_request_serializer()
        )

        filter_backends = get_django_filter_backends(self.get_filter_backends())
        has_filters = any(
            [
                filter_backend.get_schema_operation_parameters(self.view)
                for filter_backend in filter_backends
            ]
        )
        return has_request_body or has_filters

    def _should_add_http401_error_response(self) -> bool:
        # empty dicts are appended to auth methods if AllowAny or
        # IsAuthenticatedOrReadOnly are in permission classes, so
        # we need to account for that.
        auth_methods = [auth_method for auth_method in self.get_auth() if auth_method]
        return bool(auth_methods)

    def _should_add_http403_error_response(self) -> bool:
        permissions = self.view.get_permissions()
        is_allow_any = len(permissions) == 1 and isinstance(permissions[0], AllowAny)
        return bool(permissions) and not is_allow_any

    def _should_add_http404_error_response(self) -> bool:
        paginator = self._get_paginator()
        paginator_can_raise_404 = isinstance(
            paginator, (PageNumberPagination, CursorPagination)
        )
        versioning_scheme_can_raise_404 = self.view.versioning_class in [
            URLPathVersioning,
            NamespaceVersioning,
            HostNameVersioning,
            QueryParameterVersioning,
        ]
        has_path_parameters = bool(
            [
                parameter
                for parameter in self._get_parameters()
                if parameter["in"] == "path"
            ]
        )
        return (
            paginator_can_raise_404
            or versioning_scheme_can_raise_404
            or has_path_parameters
        )

    def _should_add_http406_error_response(self) -> bool:
        content_negotiator = self.view.get_content_negotiator()
        return (
            isinstance(content_negotiator, DefaultContentNegotiation)
            or self.view.versioning_class == AcceptHeaderVersioning
        )

    def _should_add_http415_error_response(self) -> bool:
        """
        This is raised whenever the default content negotiator is unable to
        determine a parser. So, if the view does not have a parser that
        handles everything (media type "*/*"), then this error can be raised.
        """
        content_negotiator = self.view.get_content_negotiator()
        parsers_that_handle_everything = [
            parser for parser in self.view.get_parsers() if parser.media_type == "*/*"
        ]
        return (
            isinstance(content_negotiator, DefaultContentNegotiation)
            and not parsers_that_handle_everything
        )

    def _should_add_http429_error_response(self) -> bool:
        return bool(self.view.get_throttles())

    def _should_add_http500_error_response(self) -> bool:
        # bugs are inevitable
        return True

    def _get_error_response_serializer(self, status_code: str):
        error_schemas = package_settings.ERROR_SCHEMAS or {}
        error_schemas = {
            str(status_code): schema for status_code, schema in error_schemas
        }
        if serializer := error_schemas.get(status_code):
            return serializer

        # the user did not provide a serializer for the status code so we will
        # fall back to the default error serializers
        if status_code == "400":
            return self._get_http400_serializer()
        else:
            error_serializers = {
                "401": ErrorResponse401Serializer,
                "403": ErrorResponse403Serializer,
                "404": ErrorResponse404Serializer,
                "406": ErrorResponse406Serializer,
                "415": ErrorResponse415Serializer,
                "429": ErrorResponse429Serializer,
                "500": ErrorResponse500Serializer,
            }
            return error_serializers.get(status_code)

    def _get_http400_serializer(self):
        # using the operation id (which is unique) to generate a unique
        # component name
        operation_id = self.get_operation_id()
        component_name = f"{camelize(operation_id)}ErrorResponse400"

        http400_serializers = []
        if self._should_add_validation_error_response():
            http400_serializers.append(ValidationErrorResponseSerializer)
        if self._should_add_parse_error_response():
            http400_serializers.append(ParseErrorResponseSerializer)

        return PolymorphicProxySerializer(
            component_name=component_name,
            serializers=http400_serializers,
            resource_type_field_name="type",
        )

    def get_examples(self):
        return get_error_examples()


def get_django_filter_backends(backends):
    """determine django filter backends that raise validation errors"""
    try:
        from django_filters.rest_framework import DjangoFilterBackend
    except ImportError:
        return []

    filter_backends = [filter_backend() for filter_backend in backends]
    return [
        backend
        for backend in filter_backends
        if isinstance(backend, DjangoFilterBackend) and backend.raise_exception
    ]


def get_error_examples():
    """
    error examples for media type "application/json". The main reason for
    adding them is that they will show `"attr": null` instead of the
    auto-generated `"attr": "string"`
    """
    errors = [
        exceptions.AuthenticationFailed(),
        exceptions.NotAuthenticated(),
        exceptions.PermissionDenied(),
        exceptions.NotFound(),
        exceptions.NotAcceptable(),
        exceptions.UnsupportedMediaType("application/json"),
        exceptions.Throttled(),
        exceptions.APIException(),
    ]
    return [get_example_from_exception(error) for error in errors]


def get_example_from_exception(exc: exceptions.APIException):
    if is_client_error(exc.status_code):
        type_ = "client_error"
    else:
        type_ = "server_error"
    return OpenApiExample(
        exc.__class__.__name__,
        value={
            "type": type_,
            "errors": [{"code": exc.get_codes(), "detail": exc.detail, "attr": None}],
        },
        response_only=True,
        status_codes=[str(exc.status_code)],
    )
