from rest_framework import serializers

from flights.models import Country, City


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
