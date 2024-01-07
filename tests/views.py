from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.authentication import BasicAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView


class IntegrityErrorView(APIView):
    def post(self, request, *args, **kwargs):
        raise IntegrityError("Concurrent update prevented.")


class ErrorView(APIView):
    def get(self, request, *args, **kwargs):
        raise Exception("Internal server error.")


class ShippingAddressSerializer(serializers.Serializer):
    street_address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    zipcode = serializers.CharField()

    def validate_state(self, value):
        if value != "CA":
            raise serializers.ValidationError(
                "We do not support shipping to the provided address.",
                code="unsupported",
            )
        return value


class OrderSerializer(serializers.Serializer):
    shipping_address = ShippingAddressSerializer()


class OrderErrorView(GenericAPIView):
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=204)


class AuthErrorView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(status=204)


class CustomThrottle(BaseThrottle):
    def allow_request(self, request, view):
        return False

    def wait(self):
        return 600


class RateLimitErrorView(APIView):
    throttle_classes = [CustomThrottle]

    def get(self, request, *args, **kwargs):
        return Response(status=204)


class RecursionView(APIView):
    def get(self, request, *args, **kwargs):
        errors = [{"field": ["Some Error"]} for _ in range(1, 1000)]
        raise serializers.ValidationError(errors)
