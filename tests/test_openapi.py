import pytest
from django.contrib.auth.models import User
from django.urls import path
from django_filters import CharFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiCallback,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_serializer,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.authentication import BasicAuthentication
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.negotiation import BaseContentNegotiation, DefaultContentNegotiation
from rest_framework.pagination import (
    CursorPagination,
    LimitOffsetPagination,
    PageNumberPagination,
)
from rest_framework.parsers import BaseParser, JSONParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.versioning import AcceptHeaderVersioning, URLPathVersioning
from rest_framework.views import APIView

from drf_standardized_errors.openapi import AutoSchema
from drf_standardized_errors.openapi_serializers import ClientErrorEnum

from .utils import generate_view_schema, get_responses


class DummySerializer(serializers.Serializer):
    test = serializers.CharField()


class DummyView(APIView):
    serializer_class = DummySerializer

    def get(self, request, *args, **kwargs):
        return Response(status=204)


def test_parse_error():
    route = "parse/"
    view = DummyView.as_view(parser_classes=[JSONParser])
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "400" in responses


class CustomParser(BaseParser):
    def parse(self, stream, media_type=None, parser_context=None):
        return {}


def test_no_parse_error():
    route = "parse/"
    view = DummyView.as_view(parser_classes=[CustomParser])
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "400" not in responses


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["first_name"]
        model = User


class ValidationView(GenericAPIView):
    serializer_class = UserSerializer
    # ensure that 400 is not added due to the parser classes by using a parser
    # that does not raise a ParseError which results in adding a 400 error response
    parser_classes = [CustomParser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=204)


def test_validation_error_for_unsafe_method():
    route = "validate/"
    view = ValidationView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route, "post")
    assert "400" in responses


def test_discriminator_mapping_for_validation_serializer():
    route = "validate/"
    view = ValidationView.as_view()
    schema = generate_view_schema(route, view)

    discriminator = schema["components"]["schemas"]["ValidateCreateError"][
        "discriminator"
    ]
    assert discriminator["propertyName"] == "attr"
    mapping_fields = set(discriminator["mapping"])
    assert mapping_fields == {"non_field_errors", "first_name"}


def test_discriminator_mapping_for_http400_serializer():
    route = "validate/"
    view = ValidationView.as_view(parser_classes=[JSONParser])
    schema = generate_view_schema(route, view)

    discriminator = schema["components"]["schemas"]["ValidateCreateErrorResponse400"][
        "discriminator"
    ]
    assert discriminator["propertyName"] == "type"
    mapping_fields = set(discriminator["mapping"])
    assert mapping_fields == {"validation_error", "client_error"}


def test_no_validation_error_for_unsafe_method():
    route = "validate/"
    view = ValidationView.as_view(serializer_class=None)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route, "post")
    assert "400" not in responses


class OpenAPITypesView(GenericAPIView):
    # ensure that 400 is not added due to the parser classes by using a parser
    # that does not raise a ParseError which results in adding a 400 error response
    parser_classes = [CustomParser]

    @extend_schema(request=OpenApiTypes.OBJECT, responses={204: None})
    def post(self, request, *args, **kwargs):
        return Response(status=204)


def test_no_error_raised_when_request_serializer_is_set_as_openapi_type():
    route = "validate/"
    view = OpenAPITypesView.as_view()
    try:
        generate_view_schema(route, view)
    except Exception:
        pytest.fail(
            "Schema generation failed when using `@extend_schema(request.OpenApiTypes.OBJECT)`"
        )


class Object1Serializer(serializers.Serializer):
    type = serializers.CharField()
    field1 = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages.update(object1_code="first error")


class Object2Serializer(serializers.Serializer):
    type = serializers.CharField()
    field2 = serializers.DateField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages.update(object2_code="second error")


class PolymorphicView(GenericAPIView):
    # ensure that 400 is not added due to the parser classes by using a parser
    # that does not raise a ParseError which results in adding a 400 error response
    parser_classes = [CustomParser]

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name="Object",
            serializers={"object1": Object1Serializer, "object2": Object2Serializer},
            resource_type_field_name="type",
        ),
        responses={204: None},
    )
    def post(self, request, *args, **kwargs):
        return Response(status=204)

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name="AnotherObject",
            serializers=[Object1Serializer, Object2Serializer],
            resource_type_field_name="type",
        ),
        responses={204: None},
    )
    def patch(self, request, *args, **kwargs):
        return Response(status=204)


def test_error_codes_for_polymorphic_serializer():
    """
    For polymorphic serializers, the fields from the actual serializers are combined.
    Also, when the same field exists in multiple serializers in a polymorphic serializer,
    their error codes should be combined.

    This test checks that fields from both serializers are present. It also checks that
    the error codes of non_field_errors from both serializers are combined.
    """
    route = "validate/"
    view = PolymorphicView.as_view()
    schema = generate_view_schema(route, view)

    mapping = schema["components"]["schemas"]["ValidateCreateError"]["discriminator"][
        "mapping"
    ]
    assert set(mapping) == {"non_field_errors", "type", "field1", "field2"}

    create_error_codes = schema["components"]["schemas"][
        "ValidateCreateNonFieldErrorsErrorComponent"
    ]["properties"]["code"]["enum"]
    assert set(create_error_codes) == {
        "invalid",
        "null",
        "object1_code",
        "object2_code",
    }

    patch_error_codes = schema["components"]["schemas"][
        "ValidatePartialUpdateNonFieldErrorsErrorComponent"
    ]["properties"]["code"]["enum"]
    assert set(patch_error_codes) == {"invalid", "null", "object1_code", "object2_code"}


class CustomFilterSet(FilterSet):
    first_name = CharFilter()


class FilteringView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomFilterSet
    # ensure that 400 is not added due to the parser classes by using a parser
    # that does not raise a ParseError which results in adding a 400 error response
    parser_classes = [CustomParser]


def test_validation_error_for_list_view_with_filters():
    route = "filter/"
    view = FilteringView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "400" in responses


def test_no_validation_error_for_list_view_without_filters():
    route = "filter/"
    view = FilteringView.as_view(filter_backends=[], filterset_class=None)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "400" not in responses


class NoExceptionRaisedFilterBackend(DjangoFilterBackend):
    raise_exception = False


def test_no_validation_error_for_list_view_when_exception_is_not_raised():
    route = "filter/"
    view = FilteringView.as_view(filter_backends=[NoExceptionRaisedFilterBackend])
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "400" not in responses


def test_401_error():
    route = "auth/"
    view = DummyView.as_view(authentication_classes=[BasicAuthentication])
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "401" in responses


def test_no_401_error():
    route = "no-auth/"
    schema = generate_view_schema(route, DummyView.as_view())
    responses = get_responses(schema, route)
    assert "401" not in responses


def test_403_error():
    route = "perm-denied/"
    view = DummyView.as_view(
        authentication_classes=[BasicAuthentication],
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "403" in responses


def test_no_403_error_when_no_perm_classes():
    route = "perm-denied/"
    view = DummyView.as_view(
        authentication_classes=[BasicAuthentication], permission_classes=[]
    )
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "403" not in responses


def test_no_403_error_when_allow_any():
    route = "perm-denied/"
    view = DummyView.as_view(
        authentication_classes=[BasicAuthentication], permission_classes=[AllowAny]
    )
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "403" not in responses


def test_no_403_error_when_is_authenticated():
    route = "perm-denied/"
    view = DummyView.as_view(
        authentication_classes=[BasicAuthentication],
        permission_classes=[IsAuthenticated],
    )
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "403" not in responses


class DummyListView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response(status=204)


def test_404_error_when_using_pagination():
    route = "not-found/"
    view = DummyListView.as_view(pagination_class=PageNumberPagination)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "404" in responses

    view = DummyListView.as_view(pagination_class=CursorPagination)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "404" in responses

    view = DummyListView.as_view(pagination_class=LimitOffsetPagination)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "404" not in responses


class CustomURLPathVersioning(URLPathVersioning):
    default_version = "v1"


class CustomAcceptHeaderVersioning(AcceptHeaderVersioning):
    default_version = "v1"


def test_404_error_when_using_versioning():
    route = "api/<version>/not-found/"
    view = DummyView.as_view(versioning_class=CustomURLPathVersioning)
    schema = generate_view_schema(route, view)
    responses = schema["paths"]["/api/v1/not-found/"]["get"]["responses"]
    assert "404" in responses

    route = "not-found/"
    view = DummyView.as_view(versioning_class=CustomAcceptHeaderVersioning)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "404" not in responses


def test_404_error_when_url_parameters():
    route = "not-found/<int:pk>/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, "not-found/{id}/")
    assert "404" in responses


def test_no_404_error():
    route = "not-found/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "404" not in responses


def test_405_error():
    route = "method-not-allowed/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "405" in responses


class AutoSchemaNo405(AutoSchema):
    def _should_add_http405_error_response(self) -> bool:
        return False


def test_no_405_error(settings):
    settings.REST_FRAMEWORK = {
        "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
        "DEFAULT_SCHEMA_CLASS": "tests.test_openapi.AutoSchemaNo405",
    }
    route = "method-not-allowed/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "405" not in responses


class DummyContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix=None):
        return renderers[0], renderers[0].media_type


def test_406_error():
    route = "not-acceptable/"

    view = DummyView.as_view(content_negotiation_class=DefaultContentNegotiation)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "406" in responses

    view = DummyView.as_view(
        content_negotiation_class=DummyContentNegotiation,
        versioning_class=CustomAcceptHeaderVersioning,
    )
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "406" in responses

    view = DummyView.as_view(content_negotiation_class=DummyContentNegotiation)
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "406" not in responses


def test_415_error():
    route = "unsupported-media-type/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "415" in responses


class EverythingParser(BaseParser):
    media_type = "*/*"

    def parse(self, stream, media_type=None, parser_context=None):
        return {"dummy": "data"}


def test_no_415_error():
    route = "all-media-types-supported/"
    view = DummyView.as_view(parser_classes=[EverythingParser])
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "415" not in responses


class CustomAnonRateThrottle(AnonRateThrottle):
    THROTTLE_RATES = {"anon": "10/day"}


def test_429_error():
    route = "throttled/"
    view = DummyView.as_view(throttle_classes=[CustomAnonRateThrottle])
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "429" in responses


def test_500_error():
    route = "server_error/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "500" in responses


def test_no_error_responses_when_not_using_package_exception_handler(settings):
    settings.REST_FRAMEWORK = {
        "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
        "DEFAULT_SCHEMA_CLASS": "drf_standardized_errors.openapi.AutoSchema",
    }

    route = "dummy/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    for status_code in ["400", "401", "403", "404", "405", "406", "415", "429", "500"]:
        assert status_code not in responses


class Error418Serializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=[("empty_teapot", "empty_teapot")])
    detail = serializers.CharField()
    attr = serializers.CharField(allow_null=True)


class TeaPotSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ClientErrorEnum.choices)
    errors = Error418Serializer(many=True)


def test_custom_status_code(settings):
    """
    adding a serializer for a status code other than the default ones,
    should result in the status code appearing for any schema operation
    """
    codes = ["400", "401", "403", "404", "405", "406", "415", "429", "500", "418"]
    settings.DRF_STANDARDIZED_ERRORS = {
        "ALLOWED_ERROR_STATUS_CODES": codes,
        "ERROR_SCHEMAS": {"418": "tests.test_openapi.TeaPotSerializer"},
    }

    route = "custom_status_code/"
    view = DummyView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    assert "418" in responses


def test_unhandled_status_code(settings, capsys):
    """
    When adding a custom status code, it needs to be added ALLOWED_ERROR_STATUS_CODES
    and a corresponding serializer should be added to ERROR_SCHEMAS as well. Since
    it's likely someone will update ALLOWED_ERROR_STATUS_CODES but not ERROR_SCHEMAS,
    we currently issue a warning for that. This test is about ensuring that the
    warning is emitted when necessary.
    """

    codes = ["400", "401", "403", "404", "405", "406", "415", "429", "500", "499"]
    settings.DRF_STANDARDIZED_ERRORS = {"ALLOWED_ERROR_STATUS_CODES": codes}

    route = "unhandled_status_code/"
    view = DummyView.as_view()
    generate_view_schema(route, view)
    stderr = capsys.readouterr().err
    assert "drf-standardized-errors: The status code '499'" in stderr


@pytest.fixture
def patterns():
    view = ValidationView.as_view()
    return [path("post/", view), path("processing/", view), path("hook/", view)]


def test_no_warnings_by_post_processing_hook(capsys, patterns):
    generator = SchemaGenerator(patterns=patterns)
    generator.get_schema(request=None, public=True)

    stderr = capsys.readouterr().err
    assert not stderr


class CallbackSerializer(serializers.Serializer):
    callbackUrl = serializers.URLField()


class CallbackView(APIView):
    """based on the example in https://swagger.io/docs/specification/callbacks/"""

    serializer_class = CallbackSerializer

    @extend_schema(
        responses={201: None},
        callbacks=[
            OpenApiCallback(
                name="myEvent",
                path="{$request.body#/callbackUrl}",
                decorator=extend_schema(
                    request=inline_serializer(
                        "EventSerializer", fields={"message": serializers.CharField()}
                    ),
                    responses={
                        200: OpenApiResponse(
                            description="Your server returns this code if it accepts the callback"
                        )
                    },
                ),
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        return Response(status=201)


def test_callbacks_response_does_not_include_error_responses(settings):
    route = "subscribe/"
    view = CallbackView.as_view()
    schema = generate_view_schema(route, view)
    event = schema["paths"][f"/{route}"]["post"]["callbacks"]["myEvent"]
    callback_responses = event["{$request.body#/callbackUrl}"]["post"]["responses"]
    assert len(callback_responses) == 1
    assert "200" in callback_responses


class GetView(APIView):
    @extend_schema(responses={204: None})
    def get(self, request, *args, **kwargs):
        return Response(status=204)


def test_get_view_does_not_raise_missing_serializer_warning(capsys):
    """
    ensure that a warning for "Unable to guess serializer" is not raised
    on a view that defines only a get method i.e. we should not try to
    determine the request serializer when inspecting a get operation for
    possible error responses.
    """
    route = "get/"
    view = GetView.as_view()
    generate_view_schema(route, view)
    stderr = capsys.readouterr().err
    assert not stderr


def test_schema_generated(api_client):
    response = api_client.get("/schema/")
    assert response.status_code == 200


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "extend_schema_serializer_example",
            summary="short summary",
            value={"field": "specific_value"},
            response_only=True,
        ),
    ]
)
class SomeSerializer(serializers.Serializer):
    field = serializers.CharField()


class ExtendSchemaSerializerView(GenericAPIView):
    serializer_class = SomeSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance={"field": "value1"})
        return Response(serializer.data)


def test_examples_from_extend_schema_serializer_are_showing_up(api_client):
    view = ExtendSchemaSerializerView.as_view()
    schema = generate_view_schema("extend_schema_serializer/", view)
    resp200 = schema["paths"]["/extend_schema_serializer/"]["get"]["responses"]["200"]
    assert "examples" in resp200["content"]["application/json"]
    examples = resp200["content"]["application/json"]["examples"]
    assert (
        examples["ExtendSchemaSerializerExample"]["value"]["field"] == "specific_value"
    )


class CustomError403Serializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=[("perm_denied", "perm_denied")])
    detail = serializers.CharField()
    attr = serializers.CharField(allow_null=True)


class CustomErrorResponse403Serializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=ClientErrorEnum.choices)
    errors = CustomError403Serializer(many=True)


class ExpSerializer(serializers.Serializer):
    field = serializers.CharField()


class ExamplesView(GenericAPIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ExpSerializer

    @extend_schema(
        responses={
            403: OpenApiResponse(
                response=CustomErrorResponse403Serializer,
                description="Registration is disabled",
            )
        },
        examples=[
            OpenApiExample(
                "Example",
                summary="short summary",
                description="longer description",
                value={
                    "type": "client_error",
                    "errors": [
                        {
                            "code": "perm_denied",
                            "detail": "Registration is disabled.",
                            "attr": None,
                        }
                    ],
                },
                status_codes=[403],
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(instance={"field": "value1"})
        return Response(serializer.data)


def test_default_examples_are_showing_up_only_when_status_code_is_allowed(
    api_client, settings
):
    settings.DRF_STANDARDIZED_ERRORS = {"ALLOWED_ERROR_STATUS_CODES": ["403"]}

    route = "perm-denied/"
    view = ExamplesView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    examples = responses["403"]["content"]["application/json"]["examples"]
    assert "Example" in examples
    assert "PermissionDenied" in examples

    settings.DRF_STANDARDIZED_ERRORS = {"ALLOWED_ERROR_STATUS_CODES": []}
    route = "perm-denied/"
    view = ExamplesView.as_view()
    schema = generate_view_schema(route, view)
    responses = get_responses(schema, route)
    examples = responses["403"]["content"]["application/json"]["examples"]
    assert "Example" in examples
    assert "PermissionDenied" not in examples
