from rest_framework import serializers

from bookings.models import SeatClass


class SeatClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatClass
        fields = (
            "id",
            "name",
        )
