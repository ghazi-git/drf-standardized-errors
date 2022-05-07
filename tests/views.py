from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
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
