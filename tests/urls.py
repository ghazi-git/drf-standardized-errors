from django.urls import path

from .views import ErrorView, IntegrityErrorView, OrderErrorView

urlpatterns = [
    path("integrity-error/", IntegrityErrorView.as_view()),
    path("error/", ErrorView.as_view()),
    path("order-error/", OrderErrorView.as_view()),
]
