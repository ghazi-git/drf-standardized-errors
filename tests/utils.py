from drf_spectacular.validation import validate_schema


def generate_view_schema(route, view):
    from django.urls import path
    from drf_spectacular.generators import SchemaGenerator

    patterns = [path(route, view)]

    generator = SchemaGenerator(patterns=patterns)
    schema = generator.get_schema(request=None, public=True)
    validate_schema(schema)
    return schema


def get_responses(schema: dict, route: str, method="get"):
    return schema["paths"][f"/{route}"][method]["responses"]


d = {
    "openapi": "3.0.3",
    "info": {"title": "", "version": "0.0.0"},
    "paths": {
        "/auth/": {
            "get": {
                "operationId": "auth_retrieve",
                "tags": ["auth"],
                "security": [{"basicAuth": []}],
                "responses": {"200": {"description": "No response body"}},
            }
        }
    },
    "components": {
        "securitySchemes": {"basicAuth": {"type": "http", "scheme": "basic"}}
    },
}
