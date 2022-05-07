from dataclasses import asdict
from typing import List, Union

from rest_framework import exceptions
from rest_framework.status import is_client_error

from .settings import package_settings
from .types import Error, ErrorResponse, ErrorType, ExceptionHandlerContext


class ExceptionFormatter:
    def __init__(
        self,
        exc: exceptions.APIException,
        context: ExceptionHandlerContext,
        original_exc: Exception,
    ):
        self.exc = exc
        self.context = context
        self.original_exc = original_exc

    def run(self):
        """
        Entrypoint for formatting the error response.

        The default error response format is as follows:
        - type: validation_error, client_error or server_error
        - errors: list of errors where each one has:
            - code: short string describing the error. Can be used by API consumers
            to customize their behavior.
            - detail: User-friendly text describing the error.
            - attr: set only when the error type is a validation error and maps
            to the serializer field name or NON_FIELD_ERRORS_KEY.

        Only validation errors can have multiple errors. Other error types have only
        one error.
        """
        error_type = self.get_error_type()
        errors = self.get_errors()
        error_response = self.get_error_response(error_type, errors)
        return self.format_error_response(error_response)

    def get_error_type(self) -> ErrorType:
        if isinstance(self.exc, exceptions.ValidationError):
            return ErrorType.VALIDATION_ERROR
        elif is_client_error(self.exc.status_code):
            return ErrorType.CLIENT_ERROR
        else:
            return ErrorType.SERVER_ERROR

    def get_errors(self) -> List[Error]:
        """
        Account for validation errors in nested serializers by returning a list
        of errors instead of a nested dict
        """
        return flatten_errors(self.exc.detail)

    def get_error_response(
        self, error_type: ErrorType, errors: List[Error]
    ) -> ErrorResponse:
        return ErrorResponse(error_type, errors)

    def format_error_response(self, error_response: ErrorResponse):
        return asdict(error_response)


def flatten_errors(
    detail: Union[list, dict, exceptions.ErrorDetail], attr=None, index=None
) -> List[Error]:
    """
    convert this:
    {
        "password": [
            ErrorDetail("This password is too short.", code="password_too_short"),
            ErrorDetail("The password is too similar to the username.", code="password_too_similar"),
        ],
        "linked_accounts" [
            {},
            {"email": [ErrorDetail("Enter a valid email address.", code="invalid")]},
        ]
    }
    to:
    {
        "type": "validation_error",
        "errors": [
            {
                "code": "password_too_short",
                "detail": "This password is too short.",
                "attr": "password"
            },
            {
                "code": "password_too_similar",
                "detail": "The password is too similar to the username.",
                "attr": "password"
            },
            {
                "code": "invalid",
                "detail": "Enter a valid email address.",
                "attr": "linked_accounts.1.email"
            }
        ]
    }
    """

    if not detail:
        return []
    elif isinstance(detail, list):
        first_item, *rest = detail
        if not isinstance(first_item, exceptions.ErrorDetail):
            index = 0 if index is None else index + 1
            if attr:
                new_attr = f"{attr}{package_settings.NESTED_FIELD_SEPARATOR}{index}"
            else:
                new_attr = str(index)
            return flatten_errors(first_item, new_attr, index) + flatten_errors(
                rest, attr, index
            )
        else:
            return flatten_errors(first_item, attr, index) + flatten_errors(
                rest, attr, index
            )
    elif isinstance(detail, dict):
        (key, value), *rest = list(detail.items())
        if attr:
            key = f"{attr}{package_settings.NESTED_FIELD_SEPARATOR}{key}"
        return flatten_errors(value, key) + flatten_errors(dict(rest), attr)
    else:
        return [Error(detail.code, str(detail), attr)]
