import os
import pathlib
import uuid

from django.db import models
from django.utils.text import slugify


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]


class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="cities"
    )

    def __str__(self):
        return f"{self.name}, {self.country.name}"

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name"]


class Airport(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="airports"
    )
    code = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return (
            f"{self.name} ({self.code}) - {self.city.name}, "
            f"{self.city.country.name}"
        )

    class Meta:
        ordering = ["name"]


class Route(models.Model):
    source = models.ForeignKey(
        Airport, related_name="source_routes", on_delete=models.CASCADE
    )
    destination = models.ForeignKey(
        Airport, related_name="destination_routes", on_delete=models.CASCADE
    )
    distance = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.source.name} to {self.destination.name}"

    class Meta:
        ordering = ["source__name", "destination__name"]


class AirplaneType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Airplane Types"
        ordering = ["name"]


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    airplane_type = models.ForeignKey(
        AirplaneType, on_delete=models.CASCADE, related_name="airplanes"
    )

    @property
    def total_seats(self):
        return sum(
            compartment.capacity for compartment in self.compartments.all()
        )

    def __str__(self):
        return f"{self.name} - {self.airplane_type.name}"

    class Meta:
        ordering = ["name"]


class SeatClass(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Seat Classes"
        ordering = ["name"]


class Compartment(models.Model):
    airplane = models.ForeignKey(
        Airplane, on_delete=models.CASCADE, related_name="compartments"
    )
    seat_class = models.ForeignKey(
        SeatClass, on_delete=models.CASCADE, related_name="compartments"
    )
    start_row = models.PositiveIntegerField()
    end_row = models.PositiveIntegerField()
    seats_in_row = models.CharField(
        max_length=10,
        help_text="Enter the seat letters for this compartment, e.g., 'ABCDEF'"
    )

    @property
    def capacity(self):
        if self.end_row < self.start_row:
            return 0
        num_rows = (self.end_row - self.start_row) + 1
        num_seats_per_row = len(self.seats_in_row)
        return num_rows * num_seats_per_row

    def __str__(self):
        return (
            f"{self.seat_class.name} (Rows {self.start_row}-{self.end_row}) "
            f"on {self.airplane.name}"
        )

    class Meta:
        ordering = ["airplane__name", "seat_class__name"]


class CrewRole(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Crew Roles"
        ordering = ["name"]


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.ForeignKey(CrewRole, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role.name}"

    class Meta:
        verbose_name_plural = "Crew Members"
        ordering = ["last_name", "first_name"]


def airline_image_path(airline: "Airline", filename: str) -> pathlib.Path:
    _, ext = os.path.splitext(filename)
    filename = f"{slugify(airline.name)}-{uuid.uuid4()}{ext}"
    return pathlib.Path("upload/airlines") / pathlib.Path(filename)


class Airline(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)
    logo = models.ImageField(
        upload_to=airline_image_path, blank=True, null=True
    )

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ["name"]


class Flight(models.Model):
    FLIGHT_STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("on Time", "On Time"),
        ("delayed", "Delayed"),
        ("departed", "Departed"),
        ("arrived", "Arrived"),
        ("cancelled", "Cancelled"),
        ("diverted", "Diverted"),
    ]

    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="flights"
    )
    airplane = models.ForeignKey(
        Airplane, on_delete=models.CASCADE, related_name="flights"
    )
    airline = models.ForeignKey(
        Airline, on_delete=models.CASCADE, related_name="flights"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=FLIGHT_STATUS_CHOICES, default="Scheduled"
    )
    crew = models.ManyToManyField(Crew, related_name="flights")

    def __str__(self):
        return (
            f"{self.airline.name} Flight from {self.route.source.name} "
            f"to {self.route.destination.name} - {self.status}"
        )

    class Meta:
        ordering = ["departure_time"]
