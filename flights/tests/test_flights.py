import tempfile
from datetime import timedelta
from itertools import count

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient

from flights.models import (
    Country,
    City,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    CrewRole,
    Crew,
    Airline,
    Flight,
    SeatClass,
    Compartment
)
from flights.serializers import FlightDetailSerializer

country_counter = count(1)
airport_counter = count(1)
airline_counter = count(1)

FLIGHTS_URL = reverse("flights:flight-list")
COUNTRIES_URL = reverse("flights:country-list")
AIRLINES_URL = reverse("flights:airline-list")


def flight_detail_url(flight_id):
    return reverse("flights:flight-detail", args=[flight_id])


def sample_country(**params):
    unique_id = next(country_counter)
    defaults = {
        "name": "Test Country",
        "code": f"C{unique_id:02}"
    }
    defaults.update(params)
    return Country.objects.create(**defaults)


def sample_city(**params):
    if "country" not in params:
        params["country"] = sample_country()
    defaults = {"name": "Test City"}
    defaults.update(params)
    return City.objects.create(**defaults)


def sample_airport(**params):
    unique_id = next(airport_counter)
    if "city" not in params:
        params["city"] = sample_city()
    defaults = {"name": "Test Airport", "code": f"P{unique_id:02}"}
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(**params):
    unique_id = next(airline_counter)
    if "source" not in params:
        params["source"] = sample_airport(
            name="Source Airport", code=f"S{unique_id:02}"
        )
    if "destination" not in params:
        params["destination"] = sample_airport(
            name="Destination Airport", code=f"D{unique_id:02}"
        )
    defaults = {"distance": 1000}
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_airplane_type(**params):
    defaults = {"name": "Test Type"}
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params):
    if "airplane_type" not in params:
        params["airplane_type"] = sample_airplane_type()
    defaults = {"name": "Test Airplane"}
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_seat_class(**params):
    defaults = {"name": "Economy Plus", "price_multiplier": 1.5}
    defaults.update(params)
    return SeatClass.objects.create(**defaults)


def sample_crew_role(**params):
    defaults = {"name": "Pilot"}
    defaults.update(params)
    return CrewRole.objects.create(**defaults)


def sample_crew(**params):
    if "role" not in params:
        params["role"] = sample_crew_role()
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_airline(**params):
    unique_id = next(airline_counter)
    defaults = {"name": "Test Airline", "code": f"A{unique_id:02}"}
    defaults.update(params)
    return Airline.objects.create(**defaults)


def sample_flight(**params):
    if "route" not in params:
        params["route"] = sample_route()
    if "airplane" not in params:
        params["airplane"] = sample_airplane()
    if "airline" not in params:
        params["airline"] = sample_airline()

    defaults = {
        "departure_time": "2026-01-01T10:00:00Z",
        "arrival_time": "2026-01-01T12:00:00Z",
    }

    crew_data = params.pop("crew", [])

    defaults.update(params)
    flight = Flight.objects.create(**defaults)

    if crew_data:
        flight.crew.set(crew_data)

    return flight


class RouteValidationTests(TestCase):
    def setUp(self):
        self.airport_a = sample_airport(name="Airport A", code="AA1")
        self.airport_b = sample_airport(name="Airport B", code="AB2")
        self.error_class = ValueError

    def test_validate_same_airports(self):
        with self.assertRaisesMessage(
                self.error_class,
                "Source and destination airports must be different."
        ):
            Route.validate_different_airports(
                source=self.airport_a,
                destination=self.airport_a,
                error_to_raise=self.error_class
            )

    def test_validate_different_airports(self):
        Route.validate_different_airports(
            source=self.airport_a,
            destination=self.airport_b,
            error_to_raise=self.error_class
        )


class AirlineImagePathTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_upload_image_to_airline(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                AIRLINES_URL,
                {"name": "Test Airline", "code": "TAL", "logo": ntf},
                format="multipart"
            )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("logo", res.data)


class CompartmentModelTests(TestCase):
    def setUp(self):
        self.airplane = sample_airplane()
        self.seat_class = sample_seat_class()

    def test_capacity_normal_case(self):
        compartment = Compartment.objects.create(
            airplane=self.airplane,
            seat_class=self.seat_class,
            start_row=1,
            end_row=5,
            seats_in_row="ABCDEF"
        )

        expected_capacity = 5 * 6
        self.assertEqual(compartment.capacity, expected_capacity)

    def test_capacity_invalid_rows(self):
        compartment = Compartment.objects.create(
            airplane=self.airplane,
            seat_class=self.seat_class,
            start_row=10,
            end_row=5,
            seats_in_row="ABCD"
        )

        self.assertEqual(compartment.capacity, 0)


class FlightValidationTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.future_1 = self.now + timedelta(hours=2)
        self.future_2 = self.now + timedelta(hours=4)
        self.past = self.now - timedelta(hours=2)
        self.airplane = sample_airplane()
        self.error_class = ValueError

    def test_validate_time_invalid_scenarios(self):
        scenarios = [
            {
                "name": "arrival_before_departure",
                "departure": self.future_2,
                "arrival": self.future_1,
                "expected_message":
                    "Arrival time must be after departure time."
            },
            {
                "name": "arrival_equals_departure",
                "departure": self.future_1,
                "arrival": self.future_1,
                "expected_message":
                    "Arrival time must be after departure time."
            },
            {
                "name": "arrival_in_past",
                "arrival": self.past,
                "departure": self.past - timedelta(hours=1),
                "expected_message": "Arrival time must be in the future."

            },
            {
                "name": "departure_in_past",
                "departure": self.past,
                "arrival": self.future_1,
                "expected_message": "Departure time must be in the future."
            },
        ]

        for scenario in scenarios:
            with self.subTest(scenario_name=scenario['name']):
                with self.assertRaisesMessage(
                        self.error_class, scenario['expected_message']
                ):
                    Flight.validate_time(
                        status="scheduled",
                        departure_time=scenario['departure'],
                        arrival_time=scenario['arrival'],
                        error_to_raise=self.error_class
                    )

    def test_validate_time_valid(self):
        Flight.validate_time(
            status="scheduled",
            departure_time=self.future_1,
            arrival_time=self.future_2,
            error_to_raise=self.error_class
        )

    def test_validate_time_cancelled_flight(self):
        Flight.validate_time(
            status="cancelled",
            departure_time=self.future_2,
            arrival_time=self.future_1,
            error_to_raise=self.error_class
        )

    def test_validate_airplane_availability_collision(self):
        sample_flight(
            airplane=self.airplane,
            departure_time=self.future_1,
            arrival_time=self.future_2,
            status="scheduled"
        )

        overlapping_departure = self.future_1 + timedelta(hours=1)
        overlapping_arrival = self.future_2 + timedelta(hours=1)

        with self.assertRaisesMessage(
                self.error_class,
                "The airplane is already scheduled for another flight."
        ):
            Flight.validate_airplane_availability(
                airplane=self.airplane,
                departure_time=overlapping_departure,
                arrival_time=overlapping_arrival,
                status="scheduled",
                error_to_raise=self.error_class
            )

    def test_validate_airplane_availability_no_collision(self):
        non_overlapping_departure = self.future_2 + timedelta(hours=1)
        non_overlapping_arrival = non_overlapping_departure + timedelta(
            hours=2
        )

        Flight.validate_airplane_availability(
            airplane=self.airplane,
            departure_time=non_overlapping_departure,
            arrival_time=non_overlapping_arrival,
            status="scheduled",
            error_to_raise=self.error_class
        )

    def test_validate_crew_availability_collision(self):
        pilot = sample_crew()
        existing_flight = sample_flight(
            departure_time=self.future_1,
            arrival_time=self.future_2
        )
        existing_flight.crew.add(pilot)

        crew_members_to_check = Crew.objects.filter(pk=pilot.pk)
        overlapping_departure = self.future_1 + timedelta(hours=1)
        overlapping_arrival = self.future_2 + timedelta(hours=1)

        with self.assertRaisesMessage(
                self.error_class,
                f"{pilot} is already scheduled for another flight."
        ):
            Flight.validate_crew_availability(
                crew_members=crew_members_to_check,
                departure_time=overlapping_departure,
                arrival_time=overlapping_arrival,
                status="scheduled",
                error_to_raise=ValueError
            )

    def test_validate_crew_availability_no_collision(self):
        pilot_on_flight = sample_crew(
            first_name="Jane", last_name="Smith"
        )

        existing_flight = sample_flight(
            departure_time=self.future_1,
            arrival_time=self.future_2,
            status="scheduled"
        )
        existing_flight.crew.add(pilot_on_flight)

        non_overlapping_departure = self.future_2 + timedelta(hours=1)
        non_overlapping_arrival = non_overlapping_departure + timedelta(
            hours=2)

        Flight.validate_crew_availability(
            crew_members=Crew.objects.filter(pk=pilot_on_flight.pk),
            departure_time=non_overlapping_departure,
            arrival_time=non_overlapping_arrival,
            status="scheduled",
            error_to_raise=ValueError
        )


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_flights_is_public(self):
        sample_flight()
        res = self.client.get(FLIGHTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_flight_unauthorized(self):
        res = self.client.post(FLIGHTS_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_list_and_filter_flights(self):
        flight1 = sample_flight()
        flight2 = sample_flight(
            route=sample_route(
                source=sample_airport(name="Airport M", code="M11")
            ),
        )

        res = self.client.get(FLIGHTS_URL, {"route": flight2.route.id})

        response_ids = [flight["id"] for flight in res.data["results"]]

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(flight1.id, response_ids)
        self.assertIn(flight2.id, response_ids)
        self.assertEqual(len(res.data["results"]), 1)

    def test_retrieve_flight_detail(self):
        flight = sample_flight(crew=[sample_crew()])
        url = flight_detail_url(flight.id)
        res = self.client.get(url)

        serializer = FlightDetailSerializer(flight)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_flight_forbidden(self):
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "airline": sample_airline().id,
            "departure_time": "2026-02-01T10:00:00Z",
            "arrival_time": "2026-02-01T12:00:00Z",
            "crew": [sample_crew().id],
        }
        res = self.client.post(FLIGHTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_create_flight_with_crew(self):
        crew1 = sample_crew(first_name="Tom", last_name="Hanks")
        crew2 = sample_crew(first_name="Brad", last_name="Pitt")
        payload = {
            "route": sample_route().id,
            "airplane": sample_airplane().id,
            "airline": sample_airline().id,
            "departure_time": "2026-02-01T10:00:00Z",
            "arrival_time": "2026-02-01T12:00:00Z",
            "crew": [crew1.id, crew2.id],
        }
        res = self.client.post(FLIGHTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        flight = Flight.objects.get(id=res.data["id"])
        crew_members = flight.crew.all()

        self.assertEqual(crew_members.count(), 2)
        self.assertIn(crew1, crew_members)
        self.assertIn(crew2, crew_members)

    def test_update_flight(self):
        flight = sample_flight()
        new_airline = sample_airline(name="New Air")
        payload = {"airline": new_airline.id}
        url = flight_detail_url(flight.id)

        res = self.client.patch(url, payload)
        flight.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(flight.airline, new_airline)

    def test_delete_flight(self):
        flight = sample_flight()
        url = flight_detail_url(flight.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Flight.objects.filter(id=flight.id).exists())
