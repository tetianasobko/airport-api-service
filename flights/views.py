from rest_framework import viewsets

from flights.models import (
    City,
    Country,
)

from flights.serializers import (
    CountrySerializer,
    CitySerializer,
    CityListSerializer,
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CityListSerializer
        return CitySerializer
