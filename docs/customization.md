# Customization

The idea behind this package is to standardize error responses and make it easier to customize. To accomplish that,
the exception handler was rewritten as a class, so it's easy to subclass and make small customizations. First, we'll
go through a brief description of the flow for generating error response, then we'll check some customizations that
you might want to make.

## Exception handling flow

You're encouraged to read the source code since it's not that much but here's a quick overview.

- The flow starts with converting known exceptions like `django.core.exceptions.PermissionDenied` and 
`django.http.Http404` to [DRF exceptions](https://www.django-rest-framework.org/api-guide/exceptions/#api-reference).
- Any unhandled exception is then converted to an instance of `rest_framework.exceptions.APIException`.
- Afterwards, the exception data is extracted and formatted, and the error response is generated with
the correct headers.
- Finally, if the exception is a server error (status code is 5xx) then it is logged and the signal
`got_request_exception` is sent out. This helps the
[django test client](https://github.com/django/django/blob/1b3c0d3b54d4ff5f75af57d3130180b1d22468e9/django/test/client.py#L712)
or an [error monitoring tool like Sentry](https://github.com/getsentry/sentry-python/blob/d880f47add3876d5cedefb4178a1dcd4d85b5d1b/sentry_sdk/integrations/django/__init__.py#L138)
capture exception details.


## Sample customizations

### Handle a non-DRF exception

This can be done the same way as what [DRF recommends](https://www.django-rest-framework.org/api-guide/exceptions/#apiexception):
- Create a new exception class by inheriting from `APIException` and setting the `default_detail` and `default_code`
attributes.
- Also, set the `status_code` attribute, but keep in mind that the status code is used to determine the error type.
A 4xx status code results in a `client_error` and a 5xx results in a `server_error`.
- In your view, you can now raise the new exception, and it will be handled appropriately.

Also, you can customize the exception handler instead of raising the new exception in your code:
- Assuming the example from DRF docs for a `ServiceUnavailable` exception
```python
from rest_framework.exceptions import APIException

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'
```
- You need to subclass `drf_standardized_errors.handler.ExceptionHandler` and override `convert_known_exceptions`
```
import requests
from drf_standardized_errors import ExceptionHandler

class MyExceptionHandler(ExceptionHandler):
    def convert_known_exceptions(self, exc: Exception) -> Exception:
        if isinstance(exc, requests.Timeout):
            return ServiceUnavailable()
        else:
            return super().convert_known_exceptions(exc)
```
Then, update the setting to point to your exception handler class
```python
DRF_STANDARDIZED_ERRORS = {"EXCEPTION_HANDLER_CLASS": "path.to.MyExceptionHandler"}
```

### Change the format of the error response

Let's say you don't need to return multiple errors, and you don't like some key names in the error response: specifically,
you want to change `detail` to `message` and `attr` to `field_name`.

You'll need to subclass `ExceptionFormatter` and override `format_error_response`.
```python
from drf_standardized_errors import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse

class MyExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        error = error_response.errors[0]
        return {
            "type": error_response.type,
            "code": error.code,
            "message": error.detail,
            "field_name": error.attr
        }
```
Then, update the corresponding setting
```python
DRF_STANDARDIZED_ERRORS = {"EXCEPTION_FORMATTER_CLASS": "path.to.MyExceptionFormatter"}
```
