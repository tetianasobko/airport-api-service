from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from airport_service.permissions import IsAdminOrOwner
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
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        queryset = self.queryset

        if self.action in ["list", "retrieve"]:
            queryset = queryset.prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
                "tickets__seat_class"
            )

        if not self.request.user.is_staff:
            queryset = self.queryset.filter(user=self.request.user)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        elif self.action == "retrieve":
            return OrderDetailSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
