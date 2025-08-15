from django.urls import path, include
from rest_framework import routers

from flights.views import (
    CountryViewSet,
    CityViewSet,
    AirportViewSet,
    RouteViewSet,
    AirplaneViewSet,
    AirplaneTypeViewSet,
    CrewRoleViewSet,
    CrewViewSet,
    AirlineViewSet,
    FlightViewSet,
    SeatClassViewSet
)

router = routers.DefaultRouter()
router.register("countries", CountryViewSet)
router.register("cities", CityViewSet)
router.register("airports", AirportViewSet)
router.register("routes", RouteViewSet)
router.register("airplane-types", AirplaneTypeViewSet)
router.register("seat-classes", SeatClassViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("crew-roles", CrewRoleViewSet)
router.register("crew", CrewViewSet)
router.register("airlines", AirlineViewSet)
router.register("flights", FlightViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "flights"
