from typing import List
from urllib.parse import urljoin

import pytest
import schemathesis
from hypothesis import settings
from schemathesis import Case


@pytest.fixture
def run_test_server(live_server, settings):
    settings.ROOT_URLCONF = "tests.fuzzing_urls"

    schema_url = urljoin(live_server.url, "/schema/")
    return schemathesis.openapi.from_url(schema_url)


schema = schemathesis.pytest.from_fixture("run_test_server")

list_field_schema = schema.include(path="/fuzzing/list_field/")
list_serializer_schema = schema.include(path="/fuzzing/list_serializer/")
dict_field_schema = schema.include(path="/fuzzing/dict_field/")


@schemathesis.hook
def before_add_examples(
    context: schemathesis.HookContext,
    examples: List[Case],
) -> None:
    operation = context.operation
    assert operation is not None

    if operation.path == "/fuzzing/list_field/":
        case = operation.Case(
            body={"field1": [None]},
            media_type="application/json",
        )
        examples.append(case)
    if operation.path == "/fuzzing/dict_field/":
        case = operation.Case(
            body={"field1": {"my_int": "non_integer_value"}},
            media_type="application/json",
        )
        examples.append(case)
    if operation.path == "/fuzzing/list_serializer/":
        case = operation.Case(
            body={"field1": [{"field2": None}]},
            media_type="application/json",
        )
        examples.append(case)


@list_field_schema.parametrize()
@settings(max_examples=100)
def test_compliance_to_api_schema_for_list_field(case):
    case.call_and_validate()


@list_serializer_schema.parametrize()
@settings(max_examples=100)
def test_compliance_to_api_schema_for_list_serializer(case):
    case.call_and_validate()


@dict_field_schema.parametrize()
@settings(max_examples=100)
def test_compliance_to_api_schema_for_dict_field(case):
    case.call_and_validate()
