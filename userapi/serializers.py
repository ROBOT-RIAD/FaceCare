from rest_framework import serializers
from account.models import User


class UserdataSerializer(serializers.Serializer):
    skin_intelligence_count = serializers.IntegerField()
    order_count = serializers.IntegerField()