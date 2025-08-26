from datetime import timedelta, date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from bookings.models import Ticket
from bookings.services import TicketPricingService
from bookings.tests.test_orders import sample_order
from flights.models import Compartment
from flights.tests.test_flights import (
    sample_airplane,
    sample_seat_class,
    sample_flight,
    sample_route,
    sample_country,
    sample_city,
    sample_airport
)


class TicketPricingServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "testuser@example.com", "testpass123"
        )
        self.order = sample_order(user=self.user)
        self.now = timezone.now()
        self.future_1 = self.now + timedelta(days=91)
        self.future_2 = self.now + timedelta(days=91, hours=2)
        self.airplane = sample_airplane()
        self.seat_class_econ = sample_seat_class(
            name="Economy", price_multiplier=1.0
        )
        self.seat_class_business = sample_seat_class(
            name="Business", price_multiplier=2.5
        )

        self.compartment = Compartment.objects.create(
            airplane=self.airplane,
            seat_class=self.seat_class_econ,
            start_row=1,
            end_row=10,
            seats_in_row="ABCDEF"
        )

        self.flight = sample_flight(
            airplane=self.airplane,
            route=sample_route(distance=1000),
            departure_time=self.future_1,
            arrival_time=self.future_2,
        )

    def test_get_base_fare(self):
        service = TicketPricingService(self.flight, self.seat_class_econ)
        expected_fare = 1000 * 0.035
        self.assertAlmostEqual(
            service._get_base_fare(), expected_fare, places=2
        )

    def test_get_seat_class_multiplier(self):
        service_econ = TicketPricingService(self.flight, self.seat_class_econ)
        service_business = TicketPricingService(
            self.flight, self.seat_class_business
        )

        self.assertEqual(service_econ._get_seat_class_multiplier(), 1.0)
        self.assertEqual(service_business._get_seat_class_multiplier(), 2.5)

    def test_get_time_multiplier_90_plus_days(self):
        flight = sample_flight(departure_time=self.future_1)
        service = TicketPricingService(flight, self.seat_class_econ)
        self.assertEqual(service._get_time_multiplier(), 1.0)

    def test_get_time_multiplier_30_to_89_days(self):
        flight_date = self.now + timedelta(days=45)
        flight = sample_flight(departure_time=flight_date)
        service = TicketPricingService(flight, self.seat_class_econ)
        self.assertEqual(service._get_time_multiplier(), 1.2)

    def test_get_time_multiplier_7_to_29_days(self):
        flight_date = self.now + timedelta(days=15)
        flight = sample_flight(departure_time=flight_date)
        service = TicketPricingService(flight, self.seat_class_econ)
        self.assertEqual(service._get_time_multiplier(), 1.5)

    def test_get_time_multiplier_less_than_7_days(self):
        flight_date = self.now + timedelta(days=5)
        flight = sample_flight(departure_time=flight_date)
        service = TicketPricingService(flight, self.seat_class_econ)
        self.assertEqual(service._get_time_multiplier(), 2.0)

    def test_get_occupancy_multiplier_low(self):
        for row in range(1, 10):
            for seat in self.compartment.seats_in_row[:3]:
                Ticket.objects.create(
                    flight=self.flight,
                    seat_class=self.seat_class_econ,
                    row=row,
                    seat=seat,
                    price=Decimal(100),
                    order=self.order
                )
        service = TicketPricingService(self.flight, self.seat_class_econ)
        self.assertEqual(service._get_occupancy_multiplier(), 1.0)

    def test_get_occupancy_multiplier_medium_low(self):
        for row in range(1, 10):
            for seat in self.compartment.seats_in_row[:4]:
                Ticket.objects.create(
                    flight=self.flight,
                    seat_class=self.seat_class_econ,
                    row=row,
                    seat=seat,
                    price=Decimal(100),
                    order=self.order
                )
        service = TicketPricingService(self.flight, self.seat_class_econ)
        self.assertEqual(service._get_occupancy_multiplier(), 1.1)

    def test_get_occupancy_multiplier_medium_high(self):
        for row in range(1, 10):
            for seat in self.compartment.seats_in_row[:5]:
                Ticket.objects.create(
                    flight=self.flight,
                    seat_class=self.seat_class_econ,
                    row=row,
                    seat=seat,
                    price=Decimal(100),
                    order=self.order
                )
        service = TicketPricingService(self.flight, self.seat_class_econ)
        self.assertEqual(service._get_occupancy_multiplier(), 1.4)

    def test_get_occupancy_multiplier_high(self):
        for row in range(1, 11):
            for seat in self.compartment.seats_in_row:
                Ticket.objects.create(
                    flight=self.flight,
                    seat_class=self.seat_class_econ,
                    row=row,
                    seat=seat,
                    price=Decimal(100),
                    order=self.order
                )
        service = TicketPricingService(self.flight, self.seat_class_econ)
        self.assertEqual(service._get_occupancy_multiplier(), 1.8)

    def test_get_occupancy_multiplier_zero_capacity(self):
        zero_capacity_comp = Compartment.objects.create(
            airplane=self.airplane,
            seat_class=sample_seat_class(
                name="Zero-Capacity", price_multiplier=1.0
            ),
            start_row=1,
            end_row=0,
            seats_in_row="ABC"
        )
        service = TicketPricingService(
            self.flight, zero_capacity_comp.seat_class
        )
        self.assertEqual(service._get_occupancy_multiplier(), 1.0)

    @patch("holidays.country_holidays")
    def test_get_holiday_multiplier_is_holiday(self, mock_holidays):
        future_date = date.today() + timedelta(days=3)
        mock_holidays.return_value = {future_date: "Test Holiday"}

        country = sample_country(code="US")
        city = sample_city(country=country)
        airport = sample_airport(city=city)
        route = sample_route(
            destination=airport
        )
        flight = sample_flight(
            route=route,
            departure_time=self.now + timedelta(days=1)
        )
        service = TicketPricingService(flight, self.seat_class_econ)

        self.assertEqual(service._get_holiday_multiplier(), 1.4)
        mock_holidays.assert_called_with("US")

    @patch("holidays.country_holidays")
    def test_get_holiday_multiplier_is_not_holiday(self, mock_holidays):
        future_date = date.today() + timedelta(days=10)
        mock_holidays.return_value = {future_date: "Test Holiday"}

        country = sample_country(code="US")
        city = sample_city(country=country)
        airport = sample_airport(city=city)
        route = sample_route(
            destination=airport
        )
        flight = sample_flight(
            route=route,
            departure_time=self.now + timedelta(days=1)
        )
        service = TicketPricingService(flight, self.seat_class_econ)

        self.assertEqual(service._get_holiday_multiplier(), 1.0)

    @patch("holidays.country_holidays")
    def test_get_holiday_multiplier_unsupported_country(self, mock_holidays):
        mock_holidays.side_effect = NotImplementedError
        country = sample_country(code="XX")
        city = sample_city(country=country)
        airport = sample_airport(city=city)
        route = sample_route(
            destination=airport
        )
        flight = sample_flight(route=route)
        service = TicketPricingService(flight, self.seat_class_econ)

        self.assertEqual(service._get_holiday_multiplier(), 1.0)
        mock_holidays.assert_called_with("XX")

    def test_calculate_price_without_luggage(self):
        base_fare = 1000 * 0.035
        service = TicketPricingService(self.flight, self.seat_class_econ)
        expected_price = Decimal(str(round(base_fare, 2)))
        self.assertEqual(
            service.calculate_price(with_luggage=False), expected_price
        )

    def test_calculate_price_with_luggage(self):
        base_fare = 1000 * 0.035
        service = TicketPricingService(self.flight, self.seat_class_econ)
        expected_price = Decimal(str(round(base_fare + 40.00, 2)))
        self.assertEqual(
            service.calculate_price(with_luggage=True), expected_price
        )
