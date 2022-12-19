# Integration wth drf-spectacular

## Configuration

Set the default schema class to the one provided by the package
```python
REST_FRAMEWORK = {
    # other settings
    "DEFAULT_SCHEMA_CLASS": "drf_standardized_errors.openapi.AutoSchema"
}
```
or on a view basis (especially if you're introducing this to a versioned API)
```python
from drf_standardized_errors.openapi import AutoSchema
from rest_framework.views import APIView

class MyAPIView(APIView):
    schema = AutoSchema()
```

Next, add the following to drf_spectacular setting `ENUM_NAME_OVERRIDES`. This will avoid multiple warnings raised
by drf-spectacular due to the same set of error codes appearing in multiple operations.
```python
SPECTACULAR_SETTINGS = {
    # other settings
    "ENUM_NAME_OVERRIDES": {
        "ValidationErrorEnum": "drf_standardized_errors.openapi_serializers.ValidationErrorEnum.values",
        "ClientErrorEnum": "drf_standardized_errors.openapi_serializers.ClientErrorEnum.values",
        "ServerErrorEnum": "drf_standardized_errors.openapi_serializers.ServerErrorEnum.values",
        "ErrorCode401Enum": "drf_standardized_errors.openapi_serializers.ErrorCode401Enum.values",
        "ErrorCode403Enum": "drf_standardized_errors.openapi_serializers.ErrorCode403Enum.values",
        "ErrorCode404Enum": "drf_standardized_errors.openapi_serializers.ErrorCode404Enum.values",
        "ErrorCode405Enum": "drf_standardized_errors.openapi_serializers.ErrorCode405Enum.values",
        "ErrorCode406Enum": "drf_standardized_errors.openapi_serializers.ErrorCode406Enum.values",
        "ErrorCode415Enum": "drf_standardized_errors.openapi_serializers.ErrorCode415Enum.values",
        "ErrorCode429Enum": "drf_standardized_errors.openapi_serializers.ErrorCode429Enum.values",
        "ErrorCode500Enum": "drf_standardized_errors.openapi_serializers.ErrorCode500Enum.values",
    },
}
```

Last, if you're not overriding the postprocessing hook setting from drf-spectacular, set it to
```python
SPECTACULAR_SETTINGS = {
    # other settings
    "POSTPROCESSING_HOOKS": ["drf_standardized_errors.openapi_hooks.postprocess_schema_enums"]
}
```
But if you're already overriding it, make sure to replace the enums postprocessing hook from drf-spectacular with
the one from this package. The hook will avoid raising warnings for dynamically created error code enums per field.

That's it, now error responses will be automatically generated for each operation in your schema. Here's
[an example](https://user-images.githubusercontent.com/17159441/172224172-b117aad2-a5cb-4172-a34a-1302f623a5a6.png)
of how it will look in swagger UI.

## Notes

- The implementation covers all the status codes returned by DRF which are: 400, 401, 403, 404, 405, 406, 415,
429 and 500. More info about each status code and the corresponding exception can be found
[here](https://www.django-rest-framework.org/api-guide/exceptions/#api-reference).
- The main goal of the current implementation is to generate a precise schema definition for validation errors. That
means **documenting all possible error codes on a field-basis**. That will help API consumers know in advance all
possible errors returned, so they can change the error messages based on the error code or execute specific logic
for a certain error code.
- The implementation includes support for django-filter when it is used. That means validation error responses
are generated for list views using the `DjangoFilterBackend` and specifying a `filterset_class` or `filterset_fields`.
- For validation errors, error codes for each serializer field are collected from the corresponding `error_messages`
attribute of that field. So, for this package to collect custom error codes, it's a good idea to follow the DRF-way
of defining and raising validation errors. Below is a sample serializer definition that would result in adding
`unknown_email_domain` to the possible error codes raised by the `email` field and `invalid_date_range` to the
list of codes associated with `non_field_errors` of the serializer. What's important is that custom error codes
are added to the `default_error_messages` of the corresponding serializer or serializer field. Note that you can
also override `__init__` and add the error codes to `self.error_messages` directly.
```python
from rest_framework.fields import empty
from rest_framework import serializers


class CustomDomainEmailField(serializers.EmailField):
    default_error_messages = {"unknown_email_domain": "The email domain is invalid."}

    def run_validation(self, data=empty):
        data = super().run_validation(data)
        if data and not data.endswith("custom-domain.com"):
            self.fail("unknown_email_domain")
        return data


class CustomSerializer(serializers.Serializer):
    default_error_messages = {
        "invalid_date_range": "The end date should be after the start date."
    }
    name = serializers.CharField()
    email = CustomDomainEmailField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.fail("invalid_date_range")

        return attrs
```


## Tips and Tricks

### Hide error responses that show in every operation

By default, the error response for all supported status codes will be added to the schema. Some of these status
codes actually appear in every operation: 500 (server error) and 405 (method not allowed). Others can also appear
in every operation under certain conditions:
- If all operations require authentication, then 401 will appear in each one of them
- If all endpoints are throttled, then the same will happen.
- Also, 406 (not acceptable) will show if you're using the default content negotiator and so on.

In that case, it is recommended to hide those error responses from the schema and leverage the schema description
attribute to cover them.

Let's take the example of an API where all endpoints require authentication and accept/return json only.
With that we have:
- 500 (server error) and 405 (method not allowed) in every operation (default package behavior)
- 401 (unauthorized) almost in every operation (aside from login/signup)
- 406 (not acceptable) appearing in every operation since the API returns json only and API consumers can populate
the "Accept" header with a value other than "application/json".
- 415 (unsupported media type) since every API consumers can send request content that is not json.

Now that we identified the error responses that will be in every operation, we can add notes about them to the
API description. Since the description can become a bit long, let's add that to a markdown file (instead of
adding it to a python file). Also, that means it will be easier to maintain. Here's a
[sample markdown file](openapi_sample_description.md) (You can copy the content from GitHub). Then, the file
contents need to be set as the API description.
```python
# settings.py
with open("/absolute/path/to/openapi_sample_description.md") as f:
    description = f.read()

SPECTACULAR_SETTINGS = {
    "TITLE": "Awesome API",
    "DESCRIPTION": description,
    # other settings
}
```

Now that the details for errors that show in all operations is part to the docs, we can remove them from the list
of errors that appear in the API schema. This should make the list of error responses
```python
DRF_STANDARDIZED_ERRORS = {
    "ALLOWED_ERROR_STATUS_CODES": ["400", "403", "404", "429"]
}
```

Note that you can limit the list of status codes even more under other circumstances. If the API uses URL versioning,
then `404` will appear in every operation. Also, if you're providing a public API and throttling all endpoints to
avoid abuse, or as part of the business model, then `429` is better removed and notes about it added to the API
description.


### Already using a custom `AutoSchema` class
If you're already overriding the `AutoSchema` class provided by drf-spectacular, be sure to inherit from the
AutoSchema class provided by this package instead. Also, if you're overriding `get_examples` and/or
`_get_response_bodies`, be sure to call `super`.


### Custom status code
This goes hand-in-hand with [handling non-DRF exceptions](customization.md#handle-a-non-drf-exception). 
So, let's assume you have defined a custom exception that could be raised in any operation:
```python
from rest_framework.exceptions import APIException

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'
```

Next, you'll need to add the corresponding status code to the settings and define a serializer class that represents
the response returned.
```python
# serializers.py
from django.db import models
from rest_framework import serializers
from drf_standardized_errors.openapi_serializers import ServerErrorEnum

class ErrorCode503Enum(models.TextChoices):
    SERVICE_UNAVAILABLE = "service_unavailable"

class Error503Serializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=ErrorCode503Enum.choices)
    detail = serializers.CharField()
    attr = serializers.CharField(allow_null=True)

class ErrorResponse503Serializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ServerErrorEnum.choices)
    errors = Error503Serializer(many=True)
```

```python
# settings.py
DRF_STANDARDIZED_ERRORS = {
    "ALLOWED_ERROR_STATUS_CODES": ["400", "403", "404", "429", "503"],
    "ERROR_SCHEMAS": {"503": "path.to.ErrorResponse503Serializer"}
}
SPECTACULAR_SETTINGS = {
    # other settings
    "ENUM_NAME_OVERRIDES": {
        # to avoid warnings raised by drf-spectacular, add the next line
        "ErrorCode503Enum": "path.to.ErrorCode503Enum.values",
    },
}
```
If the status code only appears in specific operations, you can create your own `AutoSchema` that inherits from
the one provided by this package and then override `AutoSchema._should_add_error_response` to define the criteria
that controls the addition of the error response to the operation. For example, adding the 503 response only if
operation method is `GET` looks like this:
```python
from drf_standardized_errors.openapi import AutoSchema

class CustomAutoSchema(AutoSchema):
    def _should_add_error_response(self, responses: dict, status_code: str) -> bool:
        if status_code == "503":
            return self.method == "GET"
        else:
            return super()._should_add_error_response(responses, status_code)
```

Don't forget to update the `DEFAULT_SCHEMA_CLASS` to point to the `CustomAutoSchema` in this case
```python
REST_FRAMEWORK = {
    # other settings
    "DEFAULT_SCHEMA_CLASS": "path.to.CustomAutoSchema"
}
```


### Custom error format
This entry covers the changes required if you change the default error response format. The main idea is that
you need to provide serializers that describe each error status code in `ALLOWED_ERROR_STATUS_CODES`. Also,
you should provide examples for each status code or make sure that the default examples do not show up.

Let's continue from the example in the Customization section about [changing the error response format](customization.md#change-the-format-of-the-error-response).
The standardized error response looks like this:
```json
{
    "type": "string",
    "code": "string",
    "message": "string",
    "field_name": "string"
}
```

Now, let's say you want an accurate error response based on the status code. That means you want the schema to
show which specific types, codes and field names to expect based on the status code.
Also, to avoid the example becoming too long, the `ALLOWED_ERROR_STATUS_CODES` will be set only to
`["400", "403", "404"]`. That's because the work for other status codes will be similar to `403` and `404`.
However, error response generation for `400` is complicated compared to others and that's why it's in the list.

Let's start with the easy ones (`403` and `404`):
```python
from drf_standardized_errors.openapi_serializers import ClientErrorEnum, ErrorCode403Enum, ErrorCode404Enum
from rest_framework import serializers


class ErrorResponse403Serializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ClientErrorEnum.choices)
    code = serializers.ChoiceField(choices=ErrorCode403Enum.choices)
    message = serializers.CharField()
    field_name = serializers.CharField(allow_null=True)


class ErrorResponse404Serializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ClientErrorEnum.choices)
    code = serializers.ChoiceField(choices=ErrorCode404Enum.choices)
    message = serializers.CharField()
    field_name = serializers.CharField(allow_null=True)
```

Next, let's update the settings
```python
DRF_STANDARDIZED_ERRORS = {
    "ALLOWED_ERROR_STATUS_CODES": ["400", "403", "404"],
    "ERROR_SCHEMAS": {
        "403": "path.to.ErrorResponse403Serializer",
        "404": "path.to.ErrorResponse404Serializer",
    }
}
```

Now, let's move to `400`. This status code represents parsing errors as well as validation errors and validation
errors are dynamic based on the serializer in the corresponding operation. So, we need to create our own
`AutoSchema` class that returns the correct error response serializer based on the operation.
```python
from drf_spectacular.utils import PolymorphicProxySerializer
from drf_standardized_errors.openapi_serializers import ClientErrorEnum, ParseErrorCodeEnum, ValidationErrorEnum
from drf_standardized_errors.openapi import AutoSchema
from drf_standardized_errors.settings import package_settings
from inflection import camelize
from rest_framework import serializers


class ParseErrorResponseSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ClientErrorEnum.choices)
    code = serializers.ChoiceField(choices=ParseErrorCodeEnum.choices)
    message = serializers.CharField()
    field_name = serializers.CharField(allow_null=True)


class CustomAutoSchema(AutoSchema):
    def _get_http400_serializer(self):
        operation_id = self.get_operation_id()
        component_name = f"{camelize(operation_id)}ErrorResponse400"

        http400_serializers = []
        if self._should_add_validation_error_response():
            fields_with_error_codes = self._determine_fields_with_error_codes()
            error_serializers = [
                get_serializer_for_validation_error_response(
                    operation_id, field.name, field.error_codes
                )
                for field in fields_with_error_codes
            ]
            http400_serializers.extend(error_serializers)
        if self._should_add_parse_error_response():
            http400_serializers.append(ParseErrorResponseSerializer)

        return PolymorphicProxySerializer(
            component_name=component_name,
            serializers=http400_serializers,
            resource_type_field_name="field_name",
        )


def get_serializer_for_validation_error_response(operation_id, field, error_codes):
    field_choices = [(field, field)]
    error_code_choices = sorted(zip(error_codes, error_codes))

    camelcase_operation_id = camelize(operation_id)
    attr_with_underscores = field.replace(package_settings.NESTED_FIELD_SEPARATOR, "_")
    camelcase_attr = camelize(attr_with_underscores)
    suffix = package_settings.ERROR_COMPONENT_NAME_SUFFIX
    component_name = f"{camelcase_operation_id}{camelcase_attr}{suffix}"

    class ValidationErrorSerializer(serializers.Serializer):
        type = serializers.ChoiceField(choices=ValidationErrorEnum.choices)
        code = serializers.ChoiceField(choices=error_code_choices)
        message = serializers.CharField()
        field_name = serializers.ChoiceField(choices=field_choices)

        class Meta:
            ref_name = component_name

    return ValidationErrorSerializer
```

What remains is removing the default examples from the `AutoSchema` class or generating new ones that match the new
error response output. Removing the default examples is easy and can be done by overriding `get_examples` and
returning an empty list which leaves example generation up to the OpenAPI UI used (swagger UI, redoc, ...). But,
if you're picky about the examples and want to show that the `field_name` attribute is always `null` for errors
other than validation errors, you can provide examples. Therefore, let's go with generating new examples for
`403` and `404`.
```python
from drf_standardized_errors.openapi import AutoSchema
from rest_framework import exceptions
from drf_spectacular.utils import OpenApiExample


class CustomAutoSchema(AutoSchema):
    def get_examples(self):
        errors = [exceptions.PermissionDenied(), exceptions.NotFound()]
        return [get_example_from_exception(error) for error in errors]

def get_example_from_exception(exc: exceptions.APIException):
    return OpenApiExample(
        exc.__class__.__name__,
        value={
            "type": "client_error",
            "code": exc.get_codes(),
            "message": exc.detail,
            "field_name": None,
        },
        response_only=True,
        status_codes=[str(exc.status_code)],
    )
```


### Customize error codes on an operation basis
Determining error codes on a field-basis assumes the developer will follow the example in the last item in
[Notes](#notes). However, that won't be the case for one-off validation for a serializer field for example.

Currently, there is no easy way to update the error codes on an operation-basis. Still, you can override
`drf_standardized_errors.openapi.AutoSchema._determine_fields_with_error_codes` and make the changes you want.
```python
from typing import List
from drf_standardized_errors.openapi import AutoSchema
from drf_standardized_errors.openapi_utils import InputDataField


class CustomAutoSchema(AutoSchema):
    def _determine_fields_with_error_codes(self) -> List[InputDataField]:
        """
        At this level, you need to check for the operation in question and then identify the field
        """
        data_fields: List[InputDataField] = super()._determine_fields_with_error_codes()
        # At this level, you need to check for the operation in question, identify
        # the field to which you want to add an error code and make the change.
        # This can be sth like:
        # >>> if isinstance(self.view, SomeViewSet) and self.method == "POST":
        # Then find the field in the list of data_fields and update its `error_codes`
        # attribute.
        return data_fields
```
