from django.db import transaction
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from flights.models import (
    Airport,
    Route,
    Country,
    City,
    AirplaneType,
    Airplane,
    Airline,
    Flight,
    CrewRole,
    Crew, Compartment, SeatClass
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code"]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "country"]


class CityListSerializer(CitySerializer):
    country = CountrySerializer(read_only=True)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city"]


class AirportListSerializer(AirportSerializer):
    city = CityListSerializer(read_only=True)

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]

    def validate(self, attrs):
        data = super(RouteSerializer, self).validate(attrs)

        Route.validate_different_airports(
            attrs["source"], attrs["destination"], serializers.ValidationError
        )

        return data


class RouteListSerializer(serializers.ModelSerializer):
    source_display = serializers.SerializerMethodField()
    destination_display = serializers.SerializerMethodField()

    def get_source_display(self, obj):
        airport = obj.source
        return (
            f"{airport.name} {airport.city.name}, "
            f"{airport.city.country.name}"
        )

    def get_destination_display(self, obj):
        airport = obj.destination
        return (
            f"{airport.name} {airport.city.name}, "
            f"{airport.city.country.name}"
        )

    class Meta:
        model = Route
        fields = ["id", "source_display", "destination_display", "distance"]


class RouteDetailSerializer(RouteSerializer):
    source = AirportListSerializer(read_only=True)
    destination = AirportListSerializer(read_only=True)


class AirportDetailSerializer(AirportListSerializer):
    city = CityListSerializer(read_only=True)
    source_routes = RouteListSerializer(many=True, read_only=True)
    destination_routes = RouteListSerializer(many=True, read_only=True)

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city", "source_routes",
                  "destination_routes"]


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class SeatClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatClass
        fields = (
            "id",
            "name",
            "price_multiplier",
        )


class CompartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compartment
        fields = [
            "id",
            "seat_class",
            "start_row",
            "end_row",
            "seats_in_row",
            "capacity"
        ]


class CompartmentListSerializer(CompartmentSerializer):
    seat_class = SlugRelatedField(slug_field="name", read_only=True)


class AirplaneSerializer(serializers.ModelSerializer):
    compartments = CompartmentSerializer(many=True, read_only=False)

    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "airplane_type",
            "compartments"
        ]

    def create(self, validated_data):
        with transaction.atomic():
            compartments = validated_data.pop("compartments")
            airplane = Airplane.objects.create(**validated_data)
            for compartment_data in compartments:
                Compartment.objects.create(airplane=airplane,
                                           **compartment_data)
            return airplane


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name", read_only=True
    )

    class Meta:
        model = Airplane
        fields = ["id", "name", "airplane_type"]


class AirplaneDetailSerializer(AirplaneListSerializer):
    compartments = CompartmentListSerializer(many=True, read_only=True)

    class Meta:
        model = Airplane
        fields = [
            "id",
            "name",
            "airplane_type",
            "total_seats",
            "compartments"
        ]


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ["id", "name", "code", "logo"]


class AirlineListSerializer(AirlineSerializer):
    logo = serializers.ImageField(read_only=True)

    class Meta:
        model = Airline
        fields = ["id", "name", "code", "logo"]


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "airline",
            "departure_time",
            "arrival_time",
            "status",
            "crew"
        ]

    def validate(self, attrs):
        data = super(FlightSerializer, self).validate(attrs)

        arrival_time = attrs.get("arrival_time")
        departure_time = attrs.get("departure_time")

        flight_id = self.instance.pk if self.instance else None

        Flight.validate_time(
            status=attrs.get("status"),
            arrival_time=arrival_time,
            departure_time=departure_time,
            error_to_raise=serializers.ValidationError
        )

        Flight.validate_airplane_availability(
            airplane=attrs.get("airplane"),
            arrival_time=arrival_time,
            departure_time=departure_time,
            status=attrs.get("status"),
            flight_id=flight_id,
            error_to_raise=serializers.ValidationError
        )

        Flight.validate_crew_availability(
            crew_members=attrs.get("crew", []),
            arrival_time=arrival_time,
            departure_time=departure_time,
            status=attrs.get("status"),
            flight_id=flight_id,
            error_to_raise=serializers.ValidationError
        )

        return data


class FlightListSerializer(FlightSerializer):
    airline = AirlineListSerializer(read_only=True)
    route = RouteListSerializer(read_only=True)
    airplane_type = serializers.CharField(
        source="airplane.airplane_type.name", read_only=True
    )

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane_type",
            "airline",
            "departure_time",
            "arrival_time",
            "status",
        ]


class AirlineDetailSerializer(AirlineListSerializer):
    flights = FlightListSerializer(many=True, read_only=True)

    class Meta:
        model = Airline
        fields = ["id", "name", "code", "logo", "flights"]


class CrewRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewRole
        fields = ["id", "name"]


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "role"]


class CrewListSerializer(CrewSerializer):
    role = serializers.CharField(source="role.name", read_only=True)


class CrewDetailSerializer(CrewListSerializer):
    flights = FlightListSerializer(many=True, read_only=True)

    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "role", "flights"]


class FlightDetailSerializer(FlightListSerializer):
    route = RouteDetailSerializer(read_only=True)
    airplane = AirplaneDetailSerializer(read_only=True)
    crew = CrewListSerializer(many=True, read_only=True)

    class Meta:
        model = Flight
        fields = [
            "id",
            "route",
            "airplane",
            "airline",
            "departure_time",
            "arrival_time",
            "status",
            "crew"
        ]
