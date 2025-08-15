from rest_framework import viewsets

from flights.models import (
    City,
    Country,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    CrewRole,
    Crew,
    Airline,
    Flight,
    SeatClass
)

from flights.serializers import (
    CountrySerializer,
    CitySerializer,
    CityListSerializer,
    AirportSerializer,
    AirportListSerializer,
    RouteSerializer,
    RouteListSerializer,
    AirportDetailSerializer,
    RouteDetailSerializer,
    AirplaneTypeSerializer,
    AirplaneListSerializer,
    AirplaneSerializer,
    AirplaneDetailSerializer,
    CrewRoleSerializer,
    CrewSerializer,
    CrewListSerializer,
    CrewDetailSerializer,
    AirlineSerializer,
    AirlineListSerializer,
    AirlineDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    SeatClassSerializer
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


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        elif self.action == "retrieve":
            return AirportDetailSerializer
        return AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class SeatClassViewSet(viewsets.ModelViewSet):
    queryset = SeatClass.objects.all()
    serializer_class = SeatClassSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        elif self.action == "retrieve":
            return AirplaneDetailSerializer
        return AirplaneSerializer


class CrewRoleViewSet(viewsets.ModelViewSet):
    queryset = CrewRole.objects.all()
    serializer_class = CrewRoleSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CrewListSerializer
        elif self.action == "retrieve":
            return CrewDetailSerializer
        return CrewSerializer


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirlineListSerializer
        elif self.action == "retrieve":
            return AirlineDetailSerializer
        return AirlineSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action in "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer
