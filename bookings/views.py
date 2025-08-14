from rest_framework import viewsets

from bookings.models import SeatClass
from bookings.serializers import SeatClassSerializer


class SeatClassViewSet(viewsets.ModelViewSet):
    serializer_class = SeatClassSerializer
    queryset = SeatClass.objects.all()
