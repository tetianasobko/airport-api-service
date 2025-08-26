from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from airport_service.permissions import IsAdminOrOwner
from bookings.models import Order, Ticket
from bookings.pagination import OrderPagination
from bookings.serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer, TicketReturnSerializer
)


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
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

    @extend_schema(request=TicketReturnSerializer)
    @action(
        detail=True,
        methods=["post"],
        url_path="return-ticket",
        permission_classes=[IsAdminOrOwner]
    )
    def return_ticket(self, request, pk=None):
        order = self.get_object()
        ticket_id = request.data.get("ticket_id")

        try:
            with transaction.atomic():
                ticket = Ticket.objects.get(id=ticket_id, order=order)
                ticket.delete()
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket not found in this order."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"detail": "Ticket returned successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
