from django.urls import path
from drf_spectacular.views import SpectacularAPIView

from .views import (
    DictFieldFuzzingSerializer,
    FuzzingView,
    ListFieldFuzzingSerializer,
    ListSerializerFuzzingSerializer,
)

urlpatterns = [
    path(
        "fuzzing/list_field/",
        FuzzingView.as_view(serializer_class=ListFieldFuzzingSerializer),
    ),
    path(
        "fuzzing/list_serializer/",
        FuzzingView.as_view(serializer_class=ListSerializerFuzzingSerializer),
    ),
    path(
        "fuzzing/dict_field/",
        FuzzingView.as_view(serializer_class=DictFieldFuzzingSerializer),
    ),
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
]
