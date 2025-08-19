from django.db.models import Count, F, Sum
from django.db.models.functions import Length
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
    queryset = City.objects.select_related("country")
    serializer_class = CitySerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CityListSerializer
        return CitySerializer


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == "list":
            queryset = queryset.select_related("city__country")
        elif self.action == "retrieve":
            queryset = queryset.select_related(
                "city__country"
            ).prefetch_related(
                "source_routes", "destination_routes"
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        elif self.action == "retrieve":
            return AirportDetailSerializer
        return AirportSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related(
        "source__city__country", "destination__city__country"
    )
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

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.select_related("airplane_type")
        elif self.action == "retrieve":
            queryset = queryset.select_related(
                "airplane_type"
            ).prefetch_related(
                "compartments__seat_class"
            )
        return queryset

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
    queryset = Crew.objects.select_related("role")
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

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "flights__route__source__city__country",
                "flights__route__destination__city__country",
                "flights__airline",
                "flights__airplane__airplane_type",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return AirlineListSerializer
        elif self.action == "retrieve":
            return AirlineDetailSerializer
        return AirlineSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            "route__source__city__country",
            "route__destination__city__country",
            "airplane__airplane_type",
            "airline"
        )

        if self.action == "list":
            queryset = queryset.annotate(
                total_seats=Sum(
                    (
                            F("airplane__compartments__end_row")
                            - F("airplane__compartments__start_row") + 1
                    )
                    * Length(F("airplane__compartments__seats_in_row")),
                    distinct=True
                ),
                tickets_taken=Count("tickets", distinct=True)
            ).annotate(
                tickets_available=F("total_seats") - F("tickets_taken")
            )

            airline_id = self.request.query_params.get("airline")
            if airline_id:
                queryset = queryset.filter(airline_id=airline_id)

            route_id = self.request.query_params.get("route")
            if route_id:
                queryset = queryset.filter(route_id=route_id)

            # Filter by source airport
            source = self.request.query_params.get("source")
            if source:
                queryset = queryset.filter(route__source_id=source)

            destination = self.request.query_params.get("destination")
            if destination:
                queryset = queryset.filter(route__destination_id=destination)

            departure_date = self.request.query_params.get("departure_date")
            if departure_date:
                queryset = queryset.filter(departure_time__date=departure_date)

            arrival_date = self.request.query_params.get("arrival_date")
            if arrival_date:
                queryset = queryset.filter(arrival_time__date=arrival_date)

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "crew__role", "airplane__compartments__seat_class"
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer
