import pytest
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient

from drf_standardized_errors.formatter import flatten_errors


@pytest.fixture
def required_name_error():
    return {"name": [ErrorDetail("This field is required.", code="required")]}


def test_one_error(required_name_error):
    errors = flatten_errors(required_name_error)
    assert len(errors) == 1
    assert errors[0].code == "required"
    assert errors[0].detail == "This field is required."
    assert errors[0].attr == "name"


@pytest.fixture
def multiple_errors():
    return {
        "phone": [
            ErrorDetail(
                "The phone number entered is not valid.", code="invalid_phone_number"
            )
        ],
        "password": [
            ErrorDetail("This password is too short.", code="password_too_short"),
            ErrorDetail(
                "The password is too similar to the username.",
                code="password_too_similar",
            ),
        ],
    }


def test_multiple_errors(multiple_errors):
    errors = flatten_errors(multiple_errors)
    assert len(errors) == 3
    assert errors[0].code == "invalid_phone_number"
    assert errors[0].attr == "phone"
    assert errors[1].code == "password_too_short"
    assert errors[1].attr == "password"
    assert errors[2].code == "password_too_similar"
    assert errors[2].attr == "password"


@pytest.fixture
def nested_error():
    return {
        "shipping_address": {
            "non_field_errors": [
                ErrorDetail(
                    "We do not support shipping to the provided address.",
                    code="unsupported",
                )
            ]
        }
    }


def test_nested_error(nested_error):
    errors = flatten_errors(nested_error)
    assert len(errors) == 1
    assert errors[0].code == "unsupported"
    assert errors[0].detail == "We do not support shipping to the provided address."
    assert errors[0].attr == "shipping_address.non_field_errors"


@pytest.fixture
def list_serializer_errors():
    return [
        {
            "name": [ErrorDetail("This field is required.", code="required")],
            "email": [ErrorDetail("Enter a valid email address.", code="invalid")],
        },
        {"email": [ErrorDetail("Enter a valid email address.", code="invalid")]},
    ]


def test_list_serializer_errors(list_serializer_errors):
    errors = flatten_errors(list_serializer_errors)
    assert len(errors) == 3
    assert errors[0].code == "required"
    assert errors[0].attr == "0.name"
    assert errors[1].code == "invalid"
    assert errors[1].attr == "0.email"
    assert errors[2].code == "invalid"
    assert errors[2].attr == "1.email"


@pytest.fixture
def nested_list_serializer_error():
    return {
        "recipients": [
            {},
            {"email": [ErrorDetail("Enter a valid email address.", code="invalid")]},
        ]
    }


def test_nested_list_serializer_error(nested_list_serializer_error):
    errors = flatten_errors(nested_list_serializer_error)
    assert len(errors) == 1
    assert errors[0].code == "invalid"
    assert errors[0].detail == "Enter a valid email address."
    assert errors[0].attr == "recipients.1.email"


def test_does_not_raise_recursion_error():
    client = APIClient()
    try:
        client.get("/recursion-error/")
    except RecursionError:
        pytest.fail(
            "Failed due to a recursion error. Use an iterative approach rather than "
            "a recursive one to avoid reaching the maximum recursion depth in python."
        )


def test_exception_with_detail_empty():
    detail = {"some_field": [ErrorDetail("", code="invalid")]}
    errors = flatten_errors(detail)
    assert len(errors) == 1
    assert errors[0].attr == "some_field"
    assert errors[0].detail == ""
