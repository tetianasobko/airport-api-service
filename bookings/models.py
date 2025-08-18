from django.db import models

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
