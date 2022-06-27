# Gotchas

## Writing tests

### TL;DR

If:
- you've customized the exception handler and,
- the view raises an exception that causes a 5xx status code and,
- you're writing a test that ensures that the view will return the proper response when the exception is raised

Then, make sure to pass `raise_request_exception=False`, otherwise the test will keep failing. `raise_request_exception=False`
[allows returning a 500 response instead of raising an exception](https://docs.djangoproject.com/en/stable/topics/testing/tools/#exceptions).


### The long version

I faced this while writing a test for this package, so I wanted to share it in case someone else stumbles upon it.
I was testing a custom exception formatter to make sure it's used when set in settings and that the error response
format matches my expectation. So, here's the test

```python
# views.py
from rest_framework.views import APIView

class ErrorView(APIView):
    def get(self, request, *args, **kwargs):
        raise Exception("Internal server error.")
```

```
# urls.py
from django.urls import path

from .views import ErrorView

urlpatterns = [
    path("error/", ErrorView.as_view()),
]
```

```python
# tests.py
import pytest
from rest_framework.test import APIClient

from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


@pytest.fixture
def api_client():
    return APIClient()


def test_custom_exception_formatter_class(settings, api_client):
    settings.DRF_STANDARDIZED_ERRORS = {
        "EXCEPTION_FORMATTER_CLASS": "tests.CustomExceptionFormatter"
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
```

This test kept failing and showing a traceback including `raise Exception("Internal server error.")`.
To me, it seemed like the exception handler is not doing its job.

Running the test in debug mode, I was able to see that the response returned by the view is indeed what I expected, yet,
the test is still failing.

Looking again at the test traceback and after reading the [relevant code in django test client](https://github.com/django/django/blob/0b31e024873681e187b574fe1c4afe5e48aeeecf/django/test/client.py#L803-L810),
that's when I realized what's going on: the test client defines a receiver for the signal `got_request_exception`
and if that signal is sent, it concludes that an issue happened and raises the exception.
In my test, I was raising an `Exception("Internal server error.")` that is considered a server error so,
the signal is sent out by the exception handler and django fails the test since it receives the signal.

As for why is the signal sent out by the exception handler in the first place, that's because error monitoring tools
(like Sentry) rely on it to collect exception information and make it available through their UI. Also, and as found
during the debugging of this issue, django test client needs it to determine if the view in question has raised an
exception or not and notify the developer.

The nice thing is that [django test client allows retrieving the response without raising the exception](https://docs.djangoproject.com/en/stable/topics/testing/tools/#exceptions).
That's possible by passing `raise_request_exception=False` when instantiating the test client.
