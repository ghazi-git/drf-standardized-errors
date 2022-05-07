# Quickstart

Install with `pip`
```shell
pip install drf-standardized-errors
```

Add drf-standardized-errors to your installed apps
```python
INSTALLED_APPS = [
    # other apps
    "drf_standardized_errors",
]
```

Set the exception handler for all API views
```python
REST_FRAMEWORK = {
    # other settings
    "EXCEPTION_HANDLER": "drf_standardized_errors.exception_handler"
}
```

or on a view basis (especially if you're introducing this to a versioned API)
```python
from drf_standardized_errors import exception_handler
from rest_framework.views import APIView

class MyAPIView(APIView):
    def get_exception_handler(self):
        return exception_handler
```

Now, your API error responses for 4xx and 5xx errors, will look like this
```json
{
  "type": "validation_error",
  "errors": [
    {
      "code": "required",
      "detail": "This field is required.",
      "attr": "name"
    },
    {
      "code": "max_length",
      "detail": "Ensure this value has at most 100 characters.",
      "attr": "title"
    }
  ]
}
```
or 
```json
{
  "type": "server_error",
  "errors": [
    {
      "code": "error",
      "detail": "A server error occurred.",
      "attr": null
    }
  ]
}
```

## Important Notes

- Standardized error responses when `DEBUG=True` for **unhandled exceptions** are disabled by default. That is
to allow you to get more information out of the traceback. You can enable standardized errors instead with:
```python
DRF_STANDARDIZED_ERRORS = {"ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True}
```

- Cases where you explicitly return a response with a 4xx or 5xx status code in your `APIView` do not go through
the exception handler and thus, will not have the standardized error format. So, we recommend that you raise an
exception with
`raise APIException("Service temporarily unavailable.", code="service_unavailable")`
instead of `return Response(data, status=500)`. That way, error response formatting is handled automatically for you.
But, keep in mind that exceptions that result in 5xx response are reported to error monitoring tools (like Sentry)
if you're using one.
