# Settings

Here are all available settings with their defaults, you can override them in your project settings
```python
DRF_STANDARDIZED_ERRORS = {
    # class responsible for handling the exceptions. Can be subclassed to change
    # which exceptions are handled by default, to update which exceptions are
    # reported to error monitoring tools (like Sentry), ...
    "EXCEPTION_HANDLER_CLASS": "drf_standardized_errors.handler.ExceptionHandler",
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

    # The below settings are for OpenAPI 3 schema generation

    # ONLY the responses that correspond to these status codes will appear
    # in the API schema.
    "ALLOWED_ERROR_STATUS_CODES": [
        "400",
        "401",
        "403",
        "404",
        "405",
        "406",
        "415",
        "429",
        "500",
    ],

    # A mapping used to override the default serializers used to describe
    # the error response. The key is the status code and the value is a string
    # that represents the path to the serializer class that describes the
    # error response.
    "ERROR_SCHEMAS": None,

    # When there is a validation error in list serializers, the "attr" returned
    # will be sth like "0.email", "1.email", "2.email", ... So, this setting is
    # used to represent the error codes linked to the same field during API
    # schema generation and its value will be part of the name of the
    # corresponding error component.
    "LIST_INDEX_IN_API_SCHEMA": "INDEX",

    # When there is a validation error in a DictField with the name "extra_data",
    # the "attr" returned will be sth like "extra_data.<key1>", "extra_data.<key2>",
    # "extra_data.<key3>", ... Since the keys of a DictField are not predetermined,
    # this setting is used to represent the error codes linked to the same field
    # during API schema generation and its value will be part of the name of the
    # corresponding error component.
    "DICT_KEY_IN_API_SCHEMA": "KEY",

    # should be unique to error components since it is used to identify error
    # components generated dynamically to exclude them from being processed by
    # the postprocessing hook. This avoids raising warnings for "code" and "attr"
    # which can have the same choices across multiple serializers.
    "ERROR_COMPONENT_NAME_SUFFIX": "ErrorComponent",
}
```
