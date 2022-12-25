from django.urls import path
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema


def generate_view_schema(route, view):
    patterns = [path(route, view)]

    generator = SchemaGenerator(patterns=patterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
    return schema


def get_responses(schema: dict, route: str, method="get"):
    return schema["paths"][f"/{route}"][method]["responses"]
