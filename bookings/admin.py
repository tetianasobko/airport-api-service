from django.contrib import admin

from bookings.models import Order, Ticket


class TicketInline(admin.TabularInline):
    model = Ticket
    readonly_fields = ("price",)
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    search_fields = ("user__username",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

    inlines = [TicketInline]


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id", "row", "seat", "flight", "seat_class", "price"
    )
    search_fields = (
        "flight__airline__name",
        "flight__route__source__name",
        "flight__route__destination__name",
        "order__user__username"
    )
    list_filter = ("seat_class", "flight__departure_time")
    ordering = ("flight__departure_time", "row", "seat")
    readonly_fields = ("price",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("flight", "seat_class", "order__user")
