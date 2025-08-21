import os
import pathlib
import uuid
from datetime import datetime

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone
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

    @staticmethod
    def validate_different_airports(
            source: Airport, destination: Airport, error_to_raise
    ):
        if source == destination:
            raise error_to_raise(
                {
                    "destination": "Source and destination airports "
                                   "must be different."
                }
            )

    def clean(self):
        Route.validate_different_airports(
            self.source, self.destination, ValueError
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Route, self).save(
            force_insert, force_update, using, update_fields
        )


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
    price_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0,
    )

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
        ("on time", "On Time"),
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
        max_length=20, choices=FLIGHT_STATUS_CHOICES, default="scheduled"
    )
    crew = models.ManyToManyField(Crew, related_name="flights")

    def __str__(self):
        return (
            f"{self.airline.name} Flight from {self.route.source.name} "
            f"to {self.route.destination.name} - {self.status}"
        )

    class Meta:
        ordering = ["departure_time"]

    @staticmethod
    def validate_time(
            status: str,
            arrival_time: datetime,
            departure_time: datetime,
            error_to_raise
    ):
        if status == "cancelled":
            return

        if arrival_time <= departure_time:
            raise error_to_raise(
                {"arrival_time": "Arrival time must be after departure time."}
            )

        if arrival_time <= timezone.now():
            raise error_to_raise(
                {"arrival_time": "Arrival time must be in the future."}
            )

        if departure_time <= timezone.now():
            raise error_to_raise(
                {"departure_time": "Departure time must be in the future."}
            )

    @staticmethod
    def validate_airplane_availability(
            airplane: Airplane,
            arrival_time: datetime,
            departure_time: datetime,
            status: str,
            error_to_raise,
            flight_id: int | None = None
    ):
        if status == "cancelled":
            return

        overlapping_flights = Flight.objects.filter(
                models.Q(departure_time__lt=arrival_time)
                & models.Q(arrival_time__gt=departure_time)
                & models.Q(airplane=airplane)
        ).exclude(status="cancelled")

        if flight_id is not None:
            overlapping_flights = overlapping_flights.exclude(pk=flight_id)

        if overlapping_flights.exists():
            raise error_to_raise(
                {
                    "airplane": "The airplane is already scheduled "
                                "for another flight."
                }
            )

    @staticmethod
    def validate_crew_availability(
            crew_members: QuerySet[Crew],
            arrival_time: datetime,
            departure_time: datetime,
            status: str,
            error_to_raise,
            flight_id: int | None = None
    ):
        if status == "cancelled":
            return

        for crew_member in crew_members:
            overlapping_flights = Flight.objects.filter(
                models.Q(departure_time__lt=arrival_time)
                & models.Q(arrival_time__gt=departure_time)
                & models.Q(crew=crew_member)
            ).exclude(status="cancelled")

            if flight_id is not None:
                overlapping_flights = overlapping_flights.exclude(pk=flight_id)

            if overlapping_flights.exists():
                raise error_to_raise(
                    {
                        "crew": f"{crew_member} is already scheduled "
                                f"for another flight."
                    }
                )

    def clean(self):
        Flight.validate_time(
            status=self.status,
            arrival_time=self.arrival_time,
            departure_time=self.departure_time,
            error_to_raise=ValueError
        )

        if self.pk:
            Flight.validate_airplane_availability(
                airplane=self.airplane,
                arrival_time=self.arrival_time,
                departure_time=self.departure_time,
                status=self.status,
                flight_id=self.pk,
                error_to_raise=ValueError
            )
            Flight.validate_crew_availability(
                crew_members=self.crew.all(),
                arrival_time=self.arrival_time,
                departure_time=self.departure_time,
                status=self.status,
                flight_id=self.pk,
                error_to_raise=ValueError
            )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Flight, self).save(
            force_insert, force_update, using, update_fields
        )
