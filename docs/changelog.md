# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [UNRELEASED]

## [0.15.0] - 2025-06-09
### Added
- add support for python 3.13
- add support for django 5.2
- add support for DRF 3.16

### Changed (backward-incompatible)
- Unhandled exceptions now return a generic error message by default. This avoids unintentionally leaking
sensitive data included in the exception message. To revert to the old behavior or change the default error
message:
  - create a custom exception handler class
    ```python
    from rest_framework.exceptions import APIException
    from drf_standardized_errors.handler import ExceptionHandler
    
    class MyExceptionHandler(ExceptionHandler):
        def convert_unhandled_exceptions(self, exc: Exception) -> APIException:
            if not isinstance(exc, APIException):
                # `return APIException(detail=str(exc))` restores the old behavior 
                return APIException(detail="New error message")
            else:
                return exc
    ```
  - Then, update the settings to point to your exception handler class
    ```python
    DRF_STANDARDIZED_ERRORS = {
        # ...
        "EXCEPTION_HANDLER_CLASS": "path.to.MyExceptionHandler"
    }
    ```
- set minimum version of drf-spectacular to 0.27.1
- `drf_standardized_errors.types.ErrorType` is now the following type hint
    ```python
    from typing import Literal
    ErrorType = Literal["validation_error", "client_error", "server_error"]
    ```
    `ErrorType` was previously an enum. If you referenced its members in your code, make sure to replace their
    use cases with the newly added constants:
    ```
    from drf_standardized_errors.types import VALIDATION_ERROR, CLIENT_ERROR, SERVER_ERROR
    ErrorType.VALIDATION_ERROR --> VALIDATION_ERROR
    ErrorType.CLIENT_ERROR --> CLIENT_ERROR
    ErrorType.SERVER_ERROR --> SERVER_ERROR
    ```

## [0.14.1] - 2024-08-10
### Added
- declare support for django 5.1

### Fixed
- stop ignoring exceptions with detail as an empty string when returning api errors.

## [0.14.0] - 2024-06-19
### Added
- declare support for DRF 3.15

### Fixed
- enforce support of only drf-spectacular 0.27 and newer in pyproject.toml
- ensure examples from `@extend_schema_serializer` are not ignored when adding error response examples
- show default error response examples only when the corresponding status code is allowed
- add `"null"` to the error code enum of `non_field_errors` validation errors

## [0.13.0] - 2024-02-28
### Changed
- If you're using drf-spectacular 0.27.0 or newer, update `ENUM_NAME_OVERRIDES` entries to reference `choices`
rather than `values`. The list of overrides specific to this package should become like this:
```python
SPECTACULAR_SETTINGS = {
    # other settings
    "ENUM_NAME_OVERRIDES": {
        "ValidationErrorEnum": "drf_standardized_errors.openapi_serializers.ValidationErrorEnum.choices",
        "ClientErrorEnum": "drf_standardized_errors.openapi_serializers.ClientErrorEnum.choices",
        "ServerErrorEnum": "drf_standardized_errors.openapi_serializers.ServerErrorEnum.choices",
        "ErrorCode401Enum": "drf_standardized_errors.openapi_serializers.ErrorCode401Enum.choices",
        "ErrorCode403Enum": "drf_standardized_errors.openapi_serializers.ErrorCode403Enum.choices",
        "ErrorCode404Enum": "drf_standardized_errors.openapi_serializers.ErrorCode404Enum.choices",
        "ErrorCode405Enum": "drf_standardized_errors.openapi_serializers.ErrorCode405Enum.choices",
        "ErrorCode406Enum": "drf_standardized_errors.openapi_serializers.ErrorCode406Enum.choices",
        "ErrorCode415Enum": "drf_standardized_errors.openapi_serializers.ErrorCode415Enum.choices",
        "ErrorCode429Enum": "drf_standardized_errors.openapi_serializers.ErrorCode429Enum.choices",
        "ErrorCode500Enum": "drf_standardized_errors.openapi_serializers.ErrorCode500Enum.choices",
        # other overrides
    },
}
```

### Added
- add compatibility with drf-spectacular 0.27.x
- add support for django 5.0

### Fixed
- Ensure accurate traceback inclusion in 500 error emails sent to ADMINS by capturing the original exception information using `self.exc`. This fixes the issue where tracebacks were previously showing as None for `django version >= 4.1`.
- Handle error responses with +1000 errors

## [0.12.6] - 2023-10-25
### Added
- declare support for type checking
- add support for django 4.2
- add support for python 3.12

### Fixed
- Avoid calling `AutoSchema.get_request_serializer` when inspecting a get operation for possible error responses.

## [0.12.5] - 2023-01-14
### Added
- allow adding extra validation errors on an operation-basis using the new `@extend_validation_errors` decorator.
You can find [more information about that in the documentation](openapi.md#customize-error-codes-on-an-operation-basis).

### Fixed
- use `model._default_manager` instead of `model.objects`.
- Don't generate error responses for OpenAPI callbacks.
- Make `_should_add_http403_error_response` check if permission is `IsAuthenticated` and 
`AllowAny` via `type` instead of `isinstance`
- Don't collect error codes from nested `read_only` fields

## [0.12.4] - 2022-12-11
### Fixed
- account for specifying the request serializer as a basic type (like `OpenApiTypes.STR`) or as a
`PolymorphicProxySerializer` using `@extend_schema(request=...)` when determining error codes for validation errors.

## [0.12.3] - 2022-11-13
### Added
- add support for python 3.11

## [0.12.2] - 2022-09-25
### Added
- When a custom validator class defines a `code` attribute, add it to the list of error codes of raised by
the corresponding field.
- add support for DRF 3.14

## [0.12.1] - 2022-09-03
### Fixed
- generate the mapping for discriminator fields properly instead of showing a "null" value in the generated schema (#12).

## [0.12.0] - 2022-08-27
### Added
- add support for automatically generating error responses schema with [drf-spectacular](https://github.com/tfranzel/drf-spectacular).
Check out the [corresponding documentation page](https://drf-standardized-errors.readthedocs.io/en/latest/openapi.html)
to know more about the integration with drf-spectacular.
- add support for django 4.1

## [0.11.0] - 2022-06-24
### Changed (Backward-incompatible)
- Removed all imports from `drf_standardized_errors.__init__.py`. This avoids facing the `AppRegistryNotReady` error
in certain situations (fixes #7). This change **only affects where functions/classes are imported from**, there are
**no changes to how they work**. To upgrade to this version, you need to:
  - Update the `"EXCEPTION_HANDLER"` setting in `REST_FRAMEWORK` to `"drf_standardized_errors.handler.exception_handler"`.
  - If you imported the exception handler directly, make sure the import looks like this
  `from drf_standardized_errors.handler import exception_handler`.
  - If you imported the exception handler class, make sure the import looks like this
  `from drf_standardized_errors.handler import ExceptionHandler`.
  - If you imported the exception formatter class, make sure the import looks like this
  `from drf_standardized_errors.formatter import ExceptionFormatter`.

## [0.10.2] - 2022-05-08
### Fixed
- disable tag creation by the "create GitHub release" action since it is already created by tbump

## [0.10.1] - 2022-05-08
### Fixed
- add write permission to create release action, so it can push release notes to GitHub
- fix license badge link so it works on PyPI

## [0.10.0] - 2022-05-08
### Added

- Build the documentation automatically on every commit to the main branch. The docs are
[hosted on readthedocs](https://drf-standardized-errors.readthedocs.io/en/latest/).
- Add package metadata
- add a GitHub workflow to create a GitHub release when a new tag is pushed
- add a GitHub workflow to run tests on every push and pull request
- add test coverage

## [0.9.0] - 2022-05-07
### Added

- Common error response format for DRF-based APIs
- Easily customize the error response format.
- Handle error responses for list serializers and nested serializers. 
- Add documentation
- Add tests
- Automate release steps
