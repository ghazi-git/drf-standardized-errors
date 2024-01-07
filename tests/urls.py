from django.urls import path
from drf_spectacular.views import SpectacularAPIView

from .views import (
    AuthErrorView,
    ErrorView,
    IntegrityErrorView,
    OrderErrorView,
    RateLimitErrorView,
    RecursionView,
)

urlpatterns = [
    path("integrity-error/", IntegrityErrorView.as_view()),
    path("error/", ErrorView.as_view()),
    path("order-error/", OrderErrorView.as_view()),
    path("auth-error/", AuthErrorView.as_view()),
    path("rate-limit-error/", RateLimitErrorView.as_view()),
    path("recursion-error/", RecursionView.as_view()),
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
]
