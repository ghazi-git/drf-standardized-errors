from typing import List
from urllib.parse import urljoin

import pytest
import schemathesis
from hypothesis import settings
from schemathesis import Case, DataGenerationMethod


@pytest.fixture
def run_test_server(live_server, settings):
    settings.ROOT_URLCONF = "tests.fuzzing_urls"

    schema_url = urljoin(live_server.url, "/schema/")
    return schemathesis.from_uri(schema_url)


schema = schemathesis.from_pytest_fixture("run_test_server")


@schemathesis.hook
def before_add_examples(
    context: schemathesis.hooks.HookContext,
    examples: List[Case],
) -> None:
    if context.operation.path == "/fuzzing/list_field/":
        case = Case(
            context.operation,
            0.01,
            body={"field1": [None]},
            media_type="application/json",
        )
        examples.append(case)
    if context.operation.path == "/fuzzing/dict_field/":
        case = Case(
            context.operation,
            0.01,
            body={"field1": {"my_int": "non_integer_value"}},
            media_type="application/json",
        )
        examples.append(case)
    if context.operation.path == "/fuzzing/list_serializer/":
        case = Case(
            context.operation,
            0.01,
            body={"field1": [{"field2": None}]},
            media_type="application/json",
        )
        examples.append(case)


@schema.parametrize(
    endpoint="fuzzing/list_field/",
    data_generation_methods=[
        DataGenerationMethod.negative,
        DataGenerationMethod.positive,
    ],
)
@settings(max_examples=100)
def test_compliance_to_api_schema_for_list_field(case):
    case.call_and_validate()


@schema.parametrize(
    endpoint="fuzzing/list_serializer/",
    data_generation_methods=[
        DataGenerationMethod.negative,
        DataGenerationMethod.positive,
    ],
)
@settings(max_examples=100)
def test_compliance_to_api_schema_for_list_serializer(case):
    case.call_and_validate()


@schema.parametrize(
    endpoint="fuzzing/dict_field/",
    data_generation_methods=[
        DataGenerationMethod.negative,
        DataGenerationMethod.positive,
    ],
)
@settings(max_examples=100)
def test_compliance_to_api_schema_for_dict_field(case):
    case.call_and_validate()
