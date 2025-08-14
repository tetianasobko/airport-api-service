from django.urls import path, include
from rest_framework import routers

from bookings.views import SeatClassViewSet

router = routers.DefaultRouter()
router.register("seat-classes", SeatClassViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "bookings"
