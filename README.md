# DRF Standardized Errors

Standardize your [DRF](https://www.django-rest-framework.org/) API error responses.

By default, the API error responses (4xx and 5xx) will look like:

```json
{
  "type": "validation_error",
  "errors": [
    {
      "code": "required",
      "detail": "This field is required.",
      "attr": "name"
    }
  ]
}
```


## Features

- Highly customizable: gives you flexibility to define your own standardized error responses and override
specific aspects the exception handling process without having to rewrite everything.
- Supports nested serializers and ListSerializer errors
- Plays nicely with error monitoring tools (like Sentry, ...)


## Requirements

- python >= 3.8
- Django >= 3.2
- DRF >= 3.12


## Quickstart

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

Register the exception handler
```python
REST_FRAMEWORK = {
    # other settings
    "EXCEPTION_HANDLER": "drf_standardized_errors.exception_handler"
}
```

## Notes
Standardized error responses when `DEBUG=True` for **unhandled exceptions** are disabled by default. That is
to allow you to get more information out of the traceback. You can enable standardized errors instead with:
```python
DRF_STANDARDIZED_ERRORS = {"ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True}
```

## Licence

This project is [MIT licensed](LICENSE).
