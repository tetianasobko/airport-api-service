from django.contrib import admin

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
    Flight
)


@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city")
    search_fields = ("name", "code", "city__name", "city__country__name")
    list_filter = ("city__country",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("source", "destination", "distance")
    search_fields = ("source__name", "destination__name")
    list_filter = ("source__city__country", "destination__city__country")
    ordering = ("source__name", "destination__name")


@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ("name", "rows", "seats_in_row", "airplane_type")
    search_fields = ("name", "airplane_type__name")
    list_filter = ("airplane_type",)


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "role")
    search_fields = ("first_name", "last_name", "role__name")
    list_filter = ("role",)


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = (
        "route",
        "airplane",
        "airline",
        "departure_time",
        "arrival_time",
        "status"
    )


admin.site.register(Country)
admin.site.register(City)
admin.site.register(AirplaneType)
admin.site.register(CrewRole)
