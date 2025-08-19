from rest_framework import viewsets

from bookings.models import Order
from bookings.pagination import OrderPagination
from bookings.serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
                "tickets__seat_class"
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
