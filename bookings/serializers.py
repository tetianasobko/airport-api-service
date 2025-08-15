from django.db import transaction
from rest_framework import serializers

from bookings.models import Ticket, Order
from bookings.services import TicketPricingService
from flights.serializers import FlightListSerializer, SeatClassSerializer


class TicketSerializer(serializers.ModelSerializer):
    with_luggage = serializers.BooleanField(default=False)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "flight",
            "seat_class",
            "with_luggage",
            "price"
        )
        read_only_fields = ("id", "price")


class TicketListSerializer(serializers.ModelSerializer):
    route = serializers.CharField(source="flight.route", read_only=True)
    seat_class = SeatClassSerializer(many=False, read_only=True)

    class Meta:
        model = Ticket
        fields = (
            "id",
            "row",
            "seat",
            "route",
            "seat_class"
        )


class TicketDetailSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)
    seat_class = SeatClassSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                flight = ticket_data.get("flight")
                seat_class = ticket_data.get("seat_class")
                with_luggage = ticket_data.pop("with_luggage", False)

                pricing_service = TicketPricingService(
                    flight=flight, seat_class=seat_class
                )
                ticket_price = pricing_service.calculate_price(with_luggage)
                Ticket.objects.create(
                    order=order, price=ticket_price, **ticket_data
                )

            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
