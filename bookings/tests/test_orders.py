from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

from bookings.models import Order, Ticket
from flights.models import Compartment, Flight
from user.models import User
from flights.tests.test_flights import (
    sample_flight, sample_seat_class, sample_airplane
)

ORDER_URL = reverse("bookings:order-list")


def sample_order(user, **params):
    defaults = {"user": user}
    defaults.update(params)
    return Order.objects.create(**defaults)


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_orders_unauthorized(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_unauthorized(self):
        payload = {}
        res = self.client.post(ORDER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_order_unauthorized(self):
        user = User.objects.create_user("testuser@example.com", "testpass123")
        order = sample_order(user=user)
        url = reverse("bookings:order-detail", args=[order.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TicketValidationTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.future = self.now + timedelta(hours=2)
        self.past = self.now - timedelta(hours=2)
        self.airplane = sample_airplane()
        self.seat_class_econ = sample_seat_class(name="Economy")
        self.seat_class_first = sample_seat_class(name="First")
        self.error_class = ValueError

        Compartment.objects.create(
            airplane=self.airplane,
            seat_class=self.seat_class_econ,
            start_row=1,
            end_row=10,
            seats_in_row="ABC"
        )

        self.valid_flight = sample_flight(
            airplane=self.airplane,
            departure_time=self.future,
            arrival_time=self.future + timedelta(hours=2),
            status="scheduled"
        )

    def test_validate_seat_valid(self):
        Ticket.validate_seat(
            self.valid_flight, 5, "B", self.seat_class_econ,
            self.error_class
        )

    def test_validate_seat_invalid_row(self):
        with self.assertRaisesMessage(
                self.error_class,
                "Row 15 is not in the valid range for Economy"
        ):
            Ticket.validate_seat(
                self.valid_flight, 15, "A", self.seat_class_econ,
                self.error_class
            )

    def test_validate_seat_invalid_seat(self):
        with self.assertRaisesMessage(
                self.error_class, "Seat D is not valid for this compartment"
        ):
            Ticket.validate_seat(
                self.valid_flight, 5, "D", self.seat_class_econ,
                self.error_class
            )

    def test_validate_seat_nonexistent_seat_class_on_airplane(self):
        with self.assertRaisesMessage(
                self.error_class,
                "This seat class doesn't exist on this airplane"
        ):
            Ticket.validate_seat(
                self.valid_flight, 1, "A", self.seat_class_first,
                self.error_class
            )

    def test_validate_flight_valid(self):
        Ticket.validate_flight(self.valid_flight, self.error_class)

    def test_validate_flight_cancelled_status(self):
        self.valid_flight.status = "cancelled"
        self.valid_flight.save()
        with self.assertRaisesMessage(
                self.error_class,
                "You cannot buy tickets for a flight that is cancelled."
        ):
            Ticket.validate_flight(self.valid_flight, self.error_class)

    def test_validate_flight_departed_status(self):
        self.valid_flight.status = "departed"
        self.valid_flight.save()
        with self.assertRaisesMessage(
                self.error_class,
                "You cannot buy tickets for a flight that is departed."
        ):
            Ticket.validate_flight(self.valid_flight, self.error_class)

    def test_validate_flight_past_departure_time(self):
        past_flight = Flight(
            route=self.valid_flight.route,
            airplane=self.valid_flight.airplane,
            airline=self.valid_flight.airline,
            departure_time=self.past,
            arrival_time=self.now,
            status="scheduled"
        )
        Flight.objects.bulk_create([past_flight])

        with self.assertRaisesMessage(
                self.error_class,
                "You cannot buy tickets for a flight "
                "that has already departed."
        ):
            past_flight_from_db = Flight.objects.get(id=past_flight.id)
            Ticket.validate_flight(past_flight_from_db, self.error_class)


class TicketModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "testuser@example.com", "testpass123"
        )
        self.order = sample_order(user=self.user)
        self.airplane = sample_airplane()
        self.seat_class = sample_seat_class(name="Economy")

        Compartment.objects.create(
            airplane=self.airplane,
            seat_class=self.seat_class,
            start_row=1,
            end_row=10,
            seats_in_row="ABC"
        )

        self.flight = sample_flight(airplane=self.airplane)

    def test_ticket_unique_together_constraint(self):
        Ticket.objects.create(
            row=1,
            seat="A",
            flight=self.flight,
            seat_class=self.seat_class,
            price=100.00,
            order=self.order
        )

        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1,
                seat="A",
                flight=self.flight,
                seat_class=self.seat_class,
                price=100.00,
                order=self.order
            )
