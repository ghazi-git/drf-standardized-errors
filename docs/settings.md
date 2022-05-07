# Settings

Here are all available settings with their defaults, you can override them in your project settings
```python
DRF_STANDARDIZED_ERRORS = {
    # class responsible for handling the exceptions. Can be subclassed to change
    # which exceptions are handled by default, to update which exceptions are
    # reported to error monitoring tools (like Sentry), ...
    "EXCEPTION_HANDLER_CLASS": "drf_standardized_errors.formatter.ExceptionHandler",
    # class responsible for generating error response output. Can be subclassed
    # to change the format of the error response.
    "EXCEPTION_FORMATTER_CLASS": "drf_standardized_errors.formatter.ExceptionFormatter",
    # enable the standardized errors when DEBUG=True for unhandled exceptions.
    # By default, this is set to False so you're able to view the traceback in
    # the terminal and get more information about the exception.
    "ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": False,
    # When a validation error is raised in a nested serializer, the 'attr' key
    # of the error response will look like:
    # {field}{NESTED_FIELD_SEPARATOR}{nested_field}
    # for example: 'shipping_address.zipcode'
    "NESTED_FIELD_SEPARATOR": ".",
}
```
