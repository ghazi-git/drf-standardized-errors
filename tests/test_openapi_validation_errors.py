import pytest
from django.contrib.auth.models import Group, User
from django.views.generic import UpdateView
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import action, api_view
from rest_framework.generics import DestroyAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning
from rest_framework.viewsets import ModelViewSet

from drf_standardized_errors.openapi_validation_errors import extend_validation_errors

from .utils import generate_versioned_view_schema, generate_view_schema, get_error_codes


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["first_name"]
        model = User


@pytest.fixture
def viewset_with_extra_errors():
    @extend_validation_errors(
        ["extra_error"], field_name="first_name", actions=["create"]
    )
    class ValidationViewSet(ModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    return ValidationViewSet


def test_extra_validation_errors_to_viewset(viewset_with_extra_errors):
    """simple test for using @extend_validation_errors with ViewSets"""

    route = "validate/"
    view = viewset_with_extra_errors.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "extra_error" in error_codes


@pytest.fixture
def view_with_extra_errors():
    @extend_validation_errors(["extra_error"], field_name="first_name", methods=["put"])
    class ValidationView(UpdateAPIView):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    return ValidationView


def test_extra_validation_errors_to_view(view_with_extra_errors):
    """simple test for using @extend_validation_errors with APIViews"""

    route = "validate/"
    view = view_with_extra_errors.as_view()
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateUpdateFirstNameErrorComponent")
    assert "extra_error" in error_codes
    error_codes = get_error_codes(
        schema, "ValidatePartialUpdateFirstNameErrorComponent"
    )
    assert "extra_error" not in error_codes


@pytest.fixture
def function_based_view_with_extra_errors():
    @extend_validation_errors(
        ["extra_error"], field_name="first_name", methods=["post"]
    )
    @extend_schema(request=UserSerializer, responses={201: None})
    @api_view(http_method_names=["post"])
    def validate(request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=201)

    return validate


def test_extra_validation_errors_to_function_based_api_view(
    function_based_view_with_extra_errors,
):
    route = "validate/"
    view = function_based_view_with_extra_errors
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "extra_error" in error_codes


@pytest.fixture
def validation_viewset():
    class ValidationViewSet(ModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    return ValidationViewSet


def test_methods_case_sensitivity(validation_viewset):
    """make sure it doesn't matter if we pass 'post' or 'POST' or 'PosT'"""
    extend_validation_errors(
        ["another_code"], field_name="first_name", methods=["PosT"]
    )(validation_viewset)

    route = "validate/"
    view = validation_viewset.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "another_code" in error_codes


@pytest.fixture
def function_based_view():
    def get_users(request):
        serializer = UserSerializer(instance=User.objects.all())
        return Response(serializer.data)

    return get_users


def test_decorating_non_api_view_functions(function_based_view, capsys):
    extend_validation_errors(["new_code"])(function_based_view)
    stderr = capsys.readouterr().err
    assert "`@extend_validation_errors` can only be applied to APIViews" in stderr


@pytest.fixture
def django_class_based_view():
    class UserView(UpdateView):
        model = User
        fields = ["first_name"]

    return UserView


def test_decorating_non_api_view_classes(django_class_based_view, capsys):
    extend_validation_errors(["new_code"])(django_class_based_view)
    stderr = capsys.readouterr().err
    assert "`@extend_validation_errors` can only be applied to APIViews" in stderr


def test_not_passing_error_codes(validation_viewset, capsys):
    extend_validation_errors([])(validation_viewset)
    stderr = capsys.readouterr().err
    assert "No error codes are passed to the `@extend_validation_errors`" in stderr


def test_passing_field_name_as_none(validation_viewset):
    extend_validation_errors(["some_code"], methods=["post"])(validation_viewset)

    route = "validate/"
    view = validation_viewset.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateErrorComponent")
    assert "some_code" in error_codes


def test_passing_incorrect_action(validation_viewset, capsys):
    extend_validation_errors(["some_code"], actions=["no_action"])(validation_viewset)
    stderr = capsys.readouterr().err
    assert "not in the list of actions defined on the viewset" in stderr


@pytest.fixture
def function_based_api_view():
    @extend_schema(request=UserSerializer, responses={201: None})
    @api_view(http_method_names=["post"])
    def validate(request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=201)

    return validate


def test_passing_action_for_api_view(function_based_api_view, capsys):
    extend_validation_errors(["some_error"], actions=["some_action"])(
        function_based_api_view
    )

    stderr = capsys.readouterr().err
    warning_msg = (
        "The 'actions' argument of 'extend_validation_errors' should "
        "only be set when decorating viewsets."
    )
    assert warning_msg in stderr


@pytest.fixture
def validation_view():
    class ValidationView(UpdateAPIView):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    return ValidationView


def test_passing_incorrect_method(validation_view, capsys):
    extend_validation_errors(["some_code"], methods=["get"])(validation_view)
    stderr = capsys.readouterr().err
    assert "not in the list of allowed http methods" in stderr


def test_passing_multiple_actions(validation_viewset):
    extend_validation_errors(
        ["some_error"], field_name="first_name", actions=["create", "partial_update"]
    )(validation_viewset)

    route = "validate/"
    view = validation_viewset.as_view(
        {"post": "create", "put": "update", "patch": "partial_update"}
    )
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "some_error" in error_codes
    error_codes = get_error_codes(
        schema, "ValidatePartialUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes
    error_codes = get_error_codes(schema, "ValidateUpdateFirstNameErrorComponent")
    assert "some_error" not in error_codes


def test_passing_actions_as_none(validation_viewset):
    extend_validation_errors(["some_error"], field_name="first_name")(
        validation_viewset
    )

    route = "validate/"
    view = validation_viewset.as_view(
        {"post": "create", "put": "update", "patch": "partial_update"}
    )
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "some_error" in error_codes
    error_codes = get_error_codes(
        schema, "ValidatePartialUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes
    error_codes = get_error_codes(schema, "ValidateUpdateFirstNameErrorComponent")
    assert "some_error" in error_codes


def test_passing_multiple_methods(validation_viewset):
    extend_validation_errors(
        ["some_error"], field_name="first_name", methods=["post", "put"]
    )(validation_viewset)

    route = "validate/"
    view = validation_viewset.as_view(
        {"post": "create", "put": "update", "patch": "partial_update"}
    )
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "some_error" in error_codes
    error_codes = get_error_codes(schema, "ValidateUpdateFirstNameErrorComponent")
    assert "some_error" in error_codes
    error_codes = get_error_codes(
        schema, "ValidatePartialUpdateFirstNameErrorComponent"
    )
    assert "some_error" not in error_codes


def test_passing_methods_as_none(validation_viewset):
    extend_validation_errors(["some_error"], field_name="first_name")(
        validation_viewset
    )

    route = "validate/"
    view = validation_viewset.as_view(
        {"post": "create", "put": "update", "patch": "partial_update"}
    )
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "some_error" in error_codes
    error_codes = get_error_codes(schema, "ValidateUpdateFirstNameErrorComponent")
    assert "some_error" in error_codes
    error_codes = get_error_codes(
        schema, "ValidatePartialUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes


@pytest.fixture
def versioned_view():
    class ValidationView(UpdateAPIView):
        serializer_class = UserSerializer
        queryset = User.objects.all()
        versioning_class = URLPathVersioning

    return ValidationView


def test_passing_multiple_versions(versioned_view):
    extend_validation_errors(
        ["some_error"], field_name="first_name", versions=["v1", "v2"]
    )(versioned_view)

    view = versioned_view.as_view()

    versioned_schema = generate_versioned_view_schema(view, "v1")
    error_codes = get_error_codes(
        versioned_schema, "V1ValidateUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes

    versioned_schema = generate_versioned_view_schema(view, "v2")
    error_codes = get_error_codes(
        versioned_schema, "V2ValidateUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes

    versioned_schema = generate_versioned_view_schema(view, "v3")
    error_codes = get_error_codes(
        versioned_schema, "V3ValidateUpdateFirstNameErrorComponent"
    )
    assert "some_error" not in error_codes


def test_passing_versions_as_none(versioned_view):
    extend_validation_errors(["some_error"], field_name="first_name")(versioned_view)

    view = versioned_view.as_view()

    versioned_schema = generate_versioned_view_schema(view, "v1")
    error_codes = get_error_codes(
        versioned_schema, "V1ValidateUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes

    versioned_schema = generate_versioned_view_schema(view, "v2")
    error_codes = get_error_codes(
        versioned_schema, "V2ValidateUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes

    versioned_schema = generate_versioned_view_schema(view, "v3")
    error_codes = get_error_codes(
        versioned_schema, "V3ValidateUpdateFirstNameErrorComponent"
    )
    assert "some_error" in error_codes


def test_applying_decorator_multiple_times(validation_view):
    """all error codes should be added to corresponding fields"""
    extend_first_name_errors = extend_validation_errors(
        ["short_name"], field_name="first_name"
    )
    extend_non_field_errors = extend_validation_errors(
        ["some_error"], field_name="non_field_errors"
    )
    extend_non_field_errors(extend_first_name_errors(validation_view))

    route = "validate/"
    view = validation_view.as_view()
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateUpdateFirstNameErrorComponent")
    assert "short_name" in error_codes

    error_codes = get_error_codes(schema, "ValidateUpdateNonFieldErrorsErrorComponent")
    assert "some_error" in error_codes


def test_applying_decorator_multiple_times_same_field(validation_viewset):
    """only second_error should appear in the resulting schema"""
    add_first_error = extend_validation_errors(["first_error"], field_name="first_name")
    add_second_error = extend_validation_errors(
        ["second_error"], field_name="first_name"
    )
    add_second_error(add_first_error(validation_viewset))

    route = "validate/"
    view = validation_viewset.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "second_error" in error_codes


@pytest.fixture
def child_viewset():
    @extend_validation_errors(["parent_error"], field_name="first_name")
    class ParentViewSet(ModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    class ChildViewSet(ParentViewSet):
        pass

    return ChildViewSet


def test_inherited_validation_errors(child_viewset):
    """
    errors defined on a parent are found on the child and parent errors are
    not affected
    """
    extend_validation_errors(["child_error"], field_name="non_field_errors")(
        child_viewset
    )

    route = "validate/"
    view = child_viewset.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "parent_error" in error_codes

    error_codes = get_error_codes(schema, "ValidateCreateNonFieldErrorsErrorComponent")
    assert "child_error" in error_codes


def test_overriding_inherited_validation_errors(child_viewset):
    extend_validation_errors(["child_error"], field_name="first_name")(child_viewset)

    route = "validate/"
    view = child_viewset.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateFirstNameErrorComponent")
    assert "child_error" in error_codes
    assert "parent_error" not in error_codes


@pytest.fixture
def delete_view():
    class ValidationView(DestroyAPIView):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    return ValidationView


def test_extra_validation_errors_for_unexpected_method(delete_view):
    """
    Test that it is possible to add validation errors even for delete even though
    validation errors are auto-generated only for post,put,patch or get on a list action
    """
    extend_validation_errors(
        ["some_error"], field_name="first_name", methods=["delete"]
    )(delete_view)

    route = "validate/"
    view = delete_view.as_view()
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateDestroyFirstNameErrorComponent")
    assert "some_error" in error_codes


@pytest.fixture
def viewset_with_custom_action():
    class CustomActionViewSet(ModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.all()

        @action(methods=["get"], detail=False)
        def fetch_superusers(self, request, *args, **kwargs):
            serializer = UserSerializer(instance=User.objects.filter(is_superuser=True))
            return Response(serializer.data)

    return CustomActionViewSet


def test_extra_validation_errors_for_unexpected_action(viewset_with_custom_action):
    """
    Test that it is possible to add validation errors even for get on custom action
    even though validation errors are auto-generated only for post,put,patch or get
    on a list action
    """
    extend_validation_errors(["some_error"], field_name="first_name", methods=["get"])(
        viewset_with_custom_action
    )

    route = "superusers/"
    view = viewset_with_custom_action.as_view({"get": "fetch_superusers"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "SuperusersRetrieveFirstNameErrorComponent")
    assert "some_error" in error_codes


@pytest.fixture
def viewset_with_nested_serializer():
    class GroupSerializer(serializers.ModelSerializer):
        class Meta:
            fields = ["name"]
            model = Group

    class UserSerializer(serializers.ModelSerializer):
        groups = GroupSerializer(many=True)

        class Meta:
            fields = ["first_name", "groups"]
            model = User

    class NestedViewSet(ModelViewSet):
        serializer_class = UserSerializer
        queryset = User.objects.all()

    return NestedViewSet


def test_extra_validation_errors_for_nested_list_serializer_field(
    viewset_with_nested_serializer,
):
    extend_validation_errors(["some_error"], field_name="groups.INDEX.name")(
        viewset_with_nested_serializer
    )

    route = "validate/"
    view = viewset_with_nested_serializer.as_view({"post": "create"})
    schema = generate_view_schema(route, view)
    error_codes = get_error_codes(schema, "ValidateCreateGroupsINDEXNameErrorComponent")
    assert "some_error" in error_codes
