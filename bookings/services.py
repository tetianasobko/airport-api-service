from datetime import timedelta
from django.utils import timezone
import holidays

from flights.models import Flight, SeatClass


class TicketPricingService:
    PRICE_PER_KILOMETER = 0.015

    def __init__(self, flight: Flight, seat_class: SeatClass):
        self.flight = flight
        self.seat_class = seat_class

    def calculate_price(self, with_luggage: bool = False) -> float:
        base_fare = self._get_base_fare()
        seat_class_multiplier = self._get_seat_class_multiplier()
        time_multiplier = self._get_time_multiplier()
        occupancy_multiplier = self._get_occupancy_multiplier()
        holiday_multiplier = self._get_holiday_multiplier()
        luggage_price = 40.00

        price = (
                base_fare
                * seat_class_multiplier
                * time_multiplier
                * occupancy_multiplier
                * holiday_multiplier
        )

        if with_luggage:
            price = price + luggage_price

        return round(price, 2)

    def _get_holiday_multiplier(self) -> float:
        holiday_window_days = 7
        holiday_multiplier = 1.4

        destination_country_code = (
            self.flight.route.destination.city.country.code
        )

        try:
            country_holidays = holidays.country_holidays(
                destination_country_code
            )
        except NotImplementedError:
            return 1.0

        for i in range(1, holiday_window_days + 1):
            check_date = self.flight.departure_time.date() + timedelta(days=i)
            if check_date in country_holidays:
                return holiday_multiplier

        return 1.0

    def _get_base_fare(self) -> float:
        distance_km = self.flight.route.distance
        return float(distance_km * self.PRICE_PER_KILOMETER)

    def _get_seat_class_multiplier(self) -> float:
        return float(getattr(self.seat_class, "price_multiplier", 1.0))

    def _get_time_multiplier(self) -> float:
        days_to_departure = (self.flight.departure_time - timezone.now()).days
        if days_to_departure < 7: return 2.0
        if days_to_departure < 30: return 1.5
        if days_to_departure < 90: return 1.2
        return 1.0

    def _get_occupancy_multiplier(self) -> float:
        compartment = self.flight.airplane.compartments.get(
            seat_class=self.seat_class
        )
        capacity = compartment.capacity

        tickets_sold = self.flight.ticket_set.filter(
            seat_class=self.seat_class
        ).count()

        if capacity == 0: return 1.0
        occupancy_rate = tickets_sold / capacity
        if occupancy_rate > 0.9: return 1.8
        if occupancy_rate > 0.7: return 1.4
        if occupancy_rate > 0.5: return 1.1
        return 1.0
