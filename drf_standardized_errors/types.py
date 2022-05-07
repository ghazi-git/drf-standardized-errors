from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, TypedDict

from rest_framework.request import Request
from rest_framework.views import APIView


class ExceptionHandlerContext(TypedDict):
    view: APIView
    args: tuple
    kwargs: dict
    request: Optional[Request]


class ErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    CLIENT_ERROR = "client_error"
    SERVER_ERROR = "server_error"


@dataclass
class Error:
    code: str
    detail: str
    attr: Optional[str]


@dataclass
class ErrorResponse:
    type: ErrorType
    errors: List[Error]
