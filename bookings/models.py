from django.db import models
from django.utils import timezone

from flights.models import Flight, SeatClass, Compartment


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)

    def __str__(self):
        return (
            f"Order by {self.user.username} "
            f"on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat = models.CharField(max_length=1)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)
    seat_class = models.ForeignKey(SeatClass, on_delete=models.CASCADE)
    with_luggage = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )

    def __str__(self):
        return (
            f"Ticket for {self.flight.airline.name} Flight "
            f"from {self.flight.route.source.name} "
            f"to {self.flight.route.destination.name} - "
            f"Row {self.row}, Seat {self.seat} ({self.seat_class.name})"
        )

    class Meta:
        ordering = ["flight__departure_time", "row", "seat"]
        unique_together = ("flight", "row", "seat", "seat_class")

    @staticmethod
    def validate_seat(flight, row, seat, seat_class, error_to_raise):
        try:
            compartment = flight.airplane.compartments.get(
                seat_class=seat_class
            )
        except Compartment.DoesNotExist:
            raise error_to_raise(
                "This seat class doesn't exist on this airplane"
            )

        if row < compartment.start_row or row > compartment.end_row:
            raise error_to_raise(
                f"Row {row} is not in the valid range for {seat_class.name}"
            )

        if seat not in compartment.seats_in_row:
            raise error_to_raise(
                f"Seat {seat} is not valid for this compartment"
            )

    @staticmethod
    def validate_flight(flight: Flight, error_to_raise):
        if flight.status in ("cancelled", "departed", "arrived"):
            raise error_to_raise(
                "You cannot buy tickets for a flight that is "
                f"{flight.status}."
            )

        if flight.departure_time <= timezone.now():
            raise error_to_raise(
                "You cannot buy tickets for a flight "
                "that has already departed."
            )

    def clean(self):
        Ticket.validate_seat(
            self.flight,
            self.row,
            self.seat,
            self.seat_class,
            ValueError
        )
        Ticket.validate_flight(self.flight, ValueError)

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        self.full_clean()
        super().save(force_insert, force_update, using, update_fields)
