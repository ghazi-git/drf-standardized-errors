import sys
from unittest import mock

import pytest
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django_filters import CharFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from drf_spectacular.plumbing import build_mock_request
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.schemas.openapi import SchemaGenerator

from drf_standardized_errors.openapi_utils import (
    InputDataField,
    get_django_filter_backends,
    get_error_serializer,
    get_filter_forms,
    get_flat_serializer_fields,
    get_form_fields_with_error_codes,
    get_serializer_fields_with_error_codes,
)

from .models import Post


class NestedSerializer(serializers.Serializer):
    nested_field1 = serializers.DictField(child=serializers.CharField())
    nested_field2 = serializers.IntegerField()


class CustomSerializer(serializers.Serializer):
    field1 = serializers.CharField()
    field2 = serializers.ListField(child=serializers.IntegerField())
    field3 = NestedSerializer()
    field4 = NestedSerializer(many=True)


class CustomSerializerWithNestedReadOnly(serializers.Serializer):
    field1 = serializers.CharField()
    field2 = serializers.ListField(child=serializers.IntegerField())
    field3 = NestedSerializer(read_only=True)
    field4 = NestedSerializer(read_only=True, many=True)


def test_get_flat_serializer_fields():
    fields = get_flat_serializer_fields(CustomSerializer(many=True))
    expected_fields = {
        "non_field_errors",
        "INDEX.non_field_errors",
        "INDEX.field1",
        "INDEX.field2",
        "INDEX.field2.INDEX",
        "INDEX.field3.non_field_errors",
        "INDEX.field3.nested_field1",
        "INDEX.field3.nested_field1.KEY",
        "INDEX.field3.nested_field2",
        "INDEX.field4.non_field_errors",
        "INDEX.field4.INDEX.non_field_errors",
        "INDEX.field4.INDEX.nested_field1",
        "INDEX.field4.INDEX.nested_field1.KEY",
        "INDEX.field4.INDEX.nested_field2",
    }
    assert {field.name for field in fields} == expected_fields


def test_get_flat_serializer_fields_with_nested_read_only():
    """Check case when NestedSerializer is read-only with non read-only fields."""
    fields = get_flat_serializer_fields(CustomSerializerWithNestedReadOnly(many=True))
    expected_fields = {
        "non_field_errors",
        "INDEX.non_field_errors",
        "INDEX.field1",
        "INDEX.field2",
        "INDEX.field2.INDEX",
    }
    assert {field.name for field in fields} == expected_fields


@pytest.fixture
def char_field():
    return InputDataField(
        name="name", field=serializers.CharField(min_length=1, max_length=200)
    )


def test_char_field_error_codes(char_field):
    (field,) = get_serializer_fields_with_error_codes([char_field])
    assert field.error_codes == {
        "null",
        "required",
        "invalid",
        "blank",
        "max_length",
        "min_length",
        "surrogate_characters_not_allowed",
        "null_characters_not_allowed",
    }


@pytest.fixture
def slug_field():
    return InputDataField(
        name="title",
        field=serializers.SlugField(
            allow_null=True, allow_blank=True, allow_unicode=True
        ),
    )


def test_slug_field_error_codes(slug_field):
    (field,) = get_serializer_fields_with_error_codes([slug_field])
    assert field.error_codes == {
        "required",
        "invalid",
        "surrogate_characters_not_allowed",
        "null_characters_not_allowed",
    }


@pytest.fixture
def ip_field():
    return InputDataField(name="ip", field=serializers.IPAddressField(required=False))


def test_ip_field_error_codes(ip_field):
    (field,) = get_serializer_fields_with_error_codes([ip_field])
    assert field.error_codes == {
        "null",
        "blank",
        "invalid",
        "surrogate_characters_not_allowed",
        "null_characters_not_allowed",
    }


@pytest.fixture
def integer_field():
    return InputDataField(
        name="age",
        field=serializers.IntegerField(required=False, min_value=1, max_value=120),
    )


def test_integer_field_error_codes(integer_field):
    (field,) = get_serializer_fields_with_error_codes([integer_field])
    assert field.error_codes == {
        "null",
        "invalid",
        "max_value",
        "min_value",
        "max_string_length",
    }


@pytest.fixture
def decimal_field():
    return InputDataField(
        name="rate",
        field=serializers.DecimalField(
            max_digits=3, decimal_places=2, required=False, allow_null=True
        ),
    )


def test_decimal_field_error_codes(decimal_field):
    (field,) = get_serializer_fields_with_error_codes([decimal_field])
    assert field.error_codes == {
        "invalid",
        "max_digits",
        "max_decimal_places",
        "max_whole_digits",
        "max_string_length",
    }


@pytest.fixture
def datetime_field():
    return InputDataField(
        name="dt", field=serializers.DateTimeField(required=False, allow_null=True)
    )


def test_datetime_field_error_codes(datetime_field):
    (field,) = get_serializer_fields_with_error_codes([datetime_field])
    assert field.error_codes == {"invalid", "date", "make_aware", "overflow"}


def test_naive_datetime_field_error_codes(settings, datetime_field):
    settings.USE_TZ = False

    (field,) = get_serializer_fields_with_error_codes([datetime_field])
    assert field.error_codes == {"invalid", "date"}


@pytest.fixture
def date_field():
    return InputDataField(
        name="date", field=serializers.DateField(required=False, allow_null=True)
    )


def test_date_field_error_codes(date_field):
    (field,) = get_serializer_fields_with_error_codes([date_field])
    assert field.error_codes == {"invalid", "datetime"}


@pytest.fixture
def multiple_choice_field():
    return InputDataField(
        name="colors",
        field=serializers.MultipleChoiceField(
            required=False,
            allow_null=True,
            allow_empty=False,
            allow_blank=False,
            choices=[("blue", "Blue"), ("red", "Red")],
        ),
    )


def test_multiple_choice_field_error_codes(multiple_choice_field):
    (field,) = get_serializer_fields_with_error_codes([multiple_choice_field])
    assert field.error_codes == {"invalid_choice", "not_a_list", "empty"}


@pytest.fixture
def image_field():
    return InputDataField(
        name="image",
        field=serializers.ImageField(
            required=False,
            allow_null=True,
            max_length=100,
            validators=[FileExtensionValidator(allowed_extensions=["png"])],
        ),
    )


def test_image_field_error_codes(image_field):
    (field,) = get_serializer_fields_with_error_codes([image_field])
    assert field.error_codes == {
        "invalid",
        "no_name",
        "empty",
        "max_length",
        "invalid_image",
        "invalid_extension",
    }


@pytest.fixture
def list_field():
    return InputDataField(
        name="items", field=serializers.ListField(required=False, allow_null=True)
    )


def test_list_field_error_codes(list_field):
    (field,) = get_serializer_fields_with_error_codes([list_field])
    assert field.error_codes == {"not_a_list"}


@pytest.fixture
def m2m_field():
    return InputDataField(
        name="items",
        field=serializers.PrimaryKeyRelatedField(
            many=True, required=False, allow_empty=False, queryset=User.objects.all()
        ),
    )


def test_m2m_field_error_codes(m2m_field):
    (field,) = get_serializer_fields_with_error_codes([m2m_field])
    assert field.error_codes == {
        "null",
        "not_a_list",
        "empty",
        "incorrect_type",
        "does_not_exist",
    }


class UserSerializer(serializers.Serializer):
    name = serializers.CharField()


@pytest.fixture
def serializer():
    return InputDataField(
        name="non_field_errors", field=UserSerializer(required=True, allow_null=False)
    )


def test_top_level_non_field_errors_error_codes(serializer):
    """required and null should NOT be listed as error codes"""
    (field,) = get_serializer_fields_with_error_codes([serializer])
    assert field.error_codes == {"invalid", "null"}


@pytest.fixture
def read_only_field():
    return InputDataField(name="id", field=serializers.IntegerField(read_only=True))


def test_read_only_field_error_codes(read_only_field):
    """required and null should NOT be listed as error codes"""
    fields = get_serializer_fields_with_error_codes([read_only_field])
    assert not fields


class UniqueUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


@pytest.fixture
def unique_field():
    s = UniqueUserSerializer()
    field = list(s.fields.values())[0]
    return InputDataField(name="username", field=field)


def test_unique_field_error_codes(unique_field):
    (field,) = get_serializer_fields_with_error_codes([unique_field])
    assert field.error_codes == {
        "null",
        "required",
        "invalid",
        "blank",
        "max_length",
        "surrogate_characters_not_allowed",
        "null_characters_not_allowed",
        "unique",
    }


class ContentTypeSerializer(serializers.ModelSerializer):
    """
    The field redefinition is intentional to set fields as not required
    and test that the required error code is added to fields because
    of the unique together constraint
    """

    app_label = serializers.CharField(max_length=100, required=False)
    model = serializers.CharField(
        label="Python model class name", max_length=100, required=False
    )

    class Meta:
        model = ContentType
        fields = ["app_label", "model"]


@pytest.fixture
def unique_together():
    return get_flat_serializer_fields(ContentTypeSerializer())


def test_unique_together_error_codes(unique_together):
    non_field_errors, app_label, model = get_serializer_fields_with_error_codes(
        unique_together
    )

    assert "unique" in non_field_errors.error_codes
    assert "required" in app_label.error_codes
    assert "required" in model.error_codes


class PostSerializer(serializers.ModelSerializer):
    """
    Intentional required=False to test that the 'required' error code is added
    despite that since the fields involved in a unique for date constraint
    are enforced as required by the unique for date validator.
    """

    title = serializers.CharField(max_length=200, required=False)
    published_at = serializers.DateField(required=False)

    class Meta:
        model = Post
        fields = ["title", "published_at"]


@pytest.fixture
def unique_for_date():
    return get_flat_serializer_fields(PostSerializer())


def test_unique_for_date_error_codes(unique_for_date):
    _, title, published_at = get_serializer_fields_with_error_codes(unique_for_date)

    assert "unique" in title.error_codes
    assert "required" in title.error_codes
    assert "required" in published_at.error_codes


class OddNumberField(serializers.IntegerField):
    default_error_messages = {"even_number": "Please provide an odd number"}

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if data % 2 == 0:
            self.fail("even_number")

        return data


@pytest.fixture
def custom_serializer_field():
    return InputDataField(name="odd", field=OddNumberField())


def test_custom_serializer_field_error_codes(custom_serializer_field):
    (field,) = get_serializer_fields_with_error_codes([custom_serializer_field])

    assert "even_number" in field.error_codes


class DiagnosisValidator:
    message = "Unknown diagnosis code."
    code = "unknown_diagnosis"

    def __init__(self, known_diagnosis_codes=("G00", "G01", "G02")):
        self.known_diagnosis_codes = known_diagnosis_codes

    def __call__(self, diagnosis_code):
        if diagnosis_code not in self.known_diagnosis_codes:
            raise serializers.ValidationError(self.message, code=self.code)


@pytest.fixture
def field_with_custom_validator():
    return InputDataField(
        name="diagnosis_code",
        field=serializers.CharField(validators=[DiagnosisValidator()]),
    )


def test_field_with_custom_validator(field_with_custom_validator):
    (field,) = get_serializer_fields_with_error_codes([field_with_custom_validator])
    assert "unknown_diagnosis" in field.error_codes


def test_django_filter_not_installed(monkeypatch):
    with mock.patch.dict(sys.modules, {"django_filters.rest_framework": None}):
        backends = get_django_filter_backends([DjangoFilterBackend])
        assert not backends


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class UserFilterSet(FilterSet):
    username = CharFilter()


class FilterView(ListAPIView):
    queryset = User.objects.filter(is_superuser=True)
    serializer_class = AdminSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilterSet


@pytest.fixture
def filter_view():
    generator = SchemaGenerator()
    view = generator.create_view(FilterView.as_view(), "get")
    view.request = build_mock_request("get", "filter/", view, None)
    return view


def test_get_filter_forms(filter_view):
    (form,) = get_filter_forms(filter_view, [DjangoFilterBackend()])
    assert "username" in form.fields


@pytest.fixture
def filter_view_no_model():
    generator = SchemaGenerator()
    view = generator.create_view(FilterView.as_view(queryset=None), "get")
    view.request = build_mock_request("get", "filter/", view, None)
    return view


def test_no_filter_forms_returned(filter_view_no_model):
    filter_forms = get_filter_forms(filter_view_no_model, [DjangoFilterBackend()])
    assert not filter_forms


class CharForm(forms.Form):
    char = forms.CharField(max_length=100, min_length=2)
    slug = forms.SlugField(required=False)
    regex = forms.RegexField(r"^go")
    uuid = forms.UUIDField()
    ip = forms.GenericIPAddressField(required=False)


def test_char_fields_with_error_codes():
    (char, slug, regex, uuid, ip) = get_form_fields_with_error_codes(CharForm())

    assert char.error_codes == {
        "required",
        "null_characters_not_allowed",
        "min_length",
        "max_length",
    }
    assert slug.error_codes == {"invalid", "null_characters_not_allowed"}
    assert regex.error_codes == {"invalid", "required", "null_characters_not_allowed"}
    assert uuid.error_codes == {"invalid", "required", "null_characters_not_allowed"}
    assert ip.error_codes == {"invalid", "null_characters_not_allowed"}


class NumberForm(forms.Form):
    integer = forms.IntegerField(max_value=100, min_value=2)
    dec1 = forms.DecimalField(required=False, max_digits=4, decimal_places=2)
    dec2 = forms.DecimalField(required=False, decimal_places=2)
    dec3 = forms.DecimalField(required=False, max_digits=4)
    dec4 = forms.DecimalField(required=False)


def test_number_fields_with_error_codes():
    (integer, dec1, dec2, dec3, dec4) = get_form_fields_with_error_codes(NumberForm())

    assert integer.error_codes == {"required", "max_value", "min_value", "invalid"}
    assert dec1.error_codes == {
        "invalid",
        "max_digits",
        "max_decimal_places",
        "max_whole_digits",
    }
    assert dec2.error_codes == {"invalid", "max_decimal_places"}
    assert dec3.error_codes == {"invalid", "max_digits"}
    assert dec4.error_codes == {"invalid"}


class TemporalForm(forms.Form):
    date = forms.DateField()
    datetime = forms.DateTimeField(required=False)
    duration = forms.DurationField(required=False)


def test_temporal_fields_with_error_codes():
    (date, datetime, duration) = get_form_fields_with_error_codes(TemporalForm())

    assert date.error_codes == {"required", "invalid"}
    assert datetime.error_codes == {"invalid"}
    assert duration.error_codes == {"invalid", "overflow"}


class ImageForm(forms.Form):
    image = forms.ImageField(required=False, max_length=100)


def test_image_fields_with_error_codes():
    (image,) = get_form_fields_with_error_codes(ImageForm())

    assert image.error_codes == {
        "invalid_image",
        "invalid_extension",
        "invalid",
        "empty",
        "max_length",
        "contradiction",
    }


class ChoiceForm(forms.Form):
    COLORS = [[("red", "Red"), ("blue", "Blue")]]
    choice = forms.ChoiceField(choices=COLORS)
    multiple_choice = forms.MultipleChoiceField(required=False, choices=COLORS)


def test_choice_fields_with_error_codes():
    (choice, multiple_choice) = get_form_fields_with_error_codes(ChoiceForm())

    assert choice.error_codes == {"required", "invalid_choice"}
    assert multiple_choice.error_codes == {"invalid_choice", "invalid_list"}


class MultiValueForm(forms.Form):
    split = forms.SplitDateTimeField()
    disabled = forms.URLField(disabled=True)


def test_multi_value_fields_with_error_codes():
    (split,) = get_form_fields_with_error_codes(MultiValueForm())

    assert split.error_codes == {"required", "invalid", "invalid_date", "invalid_time"}


def test_error_component_name_suffix():
    serializer = get_error_serializer("users_create", "first_name", {"required"})
    assert serializer.Meta.ref_name.endswith("ErrorComponent")


def test_updated_error_component_name_suffix(settings):
    settings.DRF_STANDARDIZED_ERRORS = {"ERROR_COMPONENT_NAME_SUFFIX": "FaultComponent"}

    serializer = get_error_serializer("users_create", "first_name", {"required"})
    assert serializer.Meta.ref_name.endswith("FaultComponent")


def test_list_index_in_api_schema():
    fields = get_flat_serializer_fields(UserSerializer(many=True))
    expected_fields = {"non_field_errors", "INDEX.non_field_errors", "INDEX.name"}
    assert {field.name for field in fields} == expected_fields


def test_updated_list_index_in_api_schema(settings):
    settings.DRF_STANDARDIZED_ERRORS = {"LIST_INDEX_IN_API_SCHEMA": "IDX"}

    fields = get_flat_serializer_fields(UserSerializer(many=True))
    expected_fields = {"non_field_errors", "IDX.non_field_errors", "IDX.name"}
    assert {field.name for field in fields} == expected_fields


class DictSerializer(serializers.Serializer):
    d = serializers.DictField(child=serializers.IntegerField())


def test_dict_index_in_api_schema():
    fields = get_flat_serializer_fields(DictSerializer())
    expected_fields = {"non_field_errors", "d", "d.KEY"}
    assert {field.name for field in fields} == expected_fields


def test_updated_dict_index_in_api_schema(settings):
    settings.DRF_STANDARDIZED_ERRORS = {"DICT_KEY_IN_API_SCHEMA": "DICT_KEY"}

    fields = get_flat_serializer_fields(DictSerializer())
    expected_fields = {"non_field_errors", "d", "d.DICT_KEY"}
    assert {field.name for field in fields} == expected_fields
