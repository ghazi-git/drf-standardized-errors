import pytest
from rest_framework.test import APIClient, APIRequestFactory

from .views import ErrorView


@pytest.fixture
def api_client():
    return APIClient(raise_request_exception=False)


@pytest.fixture
def api_request():
    factory = APIRequestFactory()
    return factory.get("/error/")


@pytest.fixture
def exception_context(api_request):
    return {"view": ErrorView(), "args": (), "kwargs": {}, "request": api_request}


@pytest.fixture
def exc():
    return Exception("Internal server error.")
