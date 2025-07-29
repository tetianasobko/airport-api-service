from rest_framework import serializers

from flights.models import (
    Airport,
    Route,
    Country,
    City,
    AirplaneType,
    Airplane
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
    country = serializers.SlugRelatedField(slug_field="name", read_only=True)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city"]


class AirportListSerializer(AirportSerializer):
    city_country = serializers.SerializerMethodField()

    def get_city_country(self, obj):
        return f"{obj.city.name}, {obj.city.country.name}"

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city_country"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteListSerializer(serializers.ModelSerializer):
    source_display = serializers.SerializerMethodField()
    destination_display = serializers.SerializerMethodField()

    def get_source_display(self, obj):
        airport = obj.source
        return f"{airport.name} {airport.city.name}, {airport.city.country.name}"

    def get_destination_display(self, obj):
        airport = obj.destination
        return f"{airport.name} {airport.city.name}, {airport.city.country.name}"

    class Meta:
        model = Route
        fields = ["id", "source_display", "destination_display", "distance"]


class RouteDetailSerializer(RouteSerializer):
    source = AirportListSerializer(read_only=True)
    destination = AirportListSerializer(read_only=True)


class AirportDetailSerializer(AirportListSerializer):
    source_routes = RouteListSerializer(many=True, read_only=True)
    destination_routes = RouteListSerializer(many=True, read_only=True)

    class Meta:
        model = Airport
        fields = ["id", "name", "code", "city_country", "source_routes",
                  "destination_routes"]


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type"]


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name", read_only=True
    )

    class Meta:
        model = Airplane
        fields = ["id", "name", "airplane_type"]


class AirplaneDetailSerializer(AirplaneListSerializer):
    class Meta:
        model = Airplane
        fields = [
            "id", "name", "rows", "seats_in_row", "airplane_type",
            "total_seats"
        ]
