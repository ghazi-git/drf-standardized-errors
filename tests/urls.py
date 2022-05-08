from django.urls import path

from .views import (
    AuthErrorView,
    ErrorView,
    IntegrityErrorView,
    OrderErrorView,
    RateLimitErrorView,
)

urlpatterns = [
    path("integrity-error/", IntegrityErrorView.as_view()),
    path("error/", ErrorView.as_view()),
    path("order-error/", OrderErrorView.as_view()),
    path("auth-error/", AuthErrorView.as_view()),
    path("rate-limit-error/", RateLimitErrorView.as_view()),
]
