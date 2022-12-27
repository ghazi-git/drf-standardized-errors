from django.urls import path, re_path
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema


def generate_view_schema(route, view):
    patterns = [path(route, view)]

    generator = SchemaGenerator(patterns=patterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
    return schema


def generate_versioned_view_schema(view, version):
    patterns = [re_path(r"^(?P<version>(v1|v2|v3))/validate/", view)]
    generator = SchemaGenerator(patterns=patterns, api_version=version)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
    return schema


def get_responses(schema: dict, route: str, method="get"):
    return schema["paths"][f"/{route}"][method]["responses"]


def get_error_codes(api_schema, schema_name):
    return api_schema["components"]["schemas"][schema_name]["properties"]["code"][
        "enum"
    ]
