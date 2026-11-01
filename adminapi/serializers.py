from rest_framework import serializers
from account.models import User, Profile


class AdminAnotdSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)




class DailyRevenueSerializer(serializers.Serializer):
    day = serializers.IntegerField()
    date = serializers.DateField()
    revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )


class MonthlyRevenueSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    daily_revenue = DailyRevenueSerializer(many=True)


class AdminMonthlyRevenueSerializer(serializers.Serializer):
    selected_month = MonthlyRevenueSerializer()
    previous_month = MonthlyRevenueSerializer()


class AdminMonthlyRevenueQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(
        required=False,
        min_value=2000,
        max_value=9999
    )
    month = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=12
    )


class AdminLastSevenDaysOrderSerializer(serializers.Serializer):
    date = serializers.DateField()
    day = serializers.CharField()
    order_count = serializers.IntegerField()



class AdminBestSellingProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_image = serializers.URLField(allow_null=True,required=False)
    total_sold = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=12,decimal_places=2)




class AdminProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "gender",
            "contact_number",
            "skin_type",
            "date_of_birth",
            "image",
        ]


class AdminUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "profile",
        ]

    def get_profile(self, obj):
        try:
            profile = obj.profile
            return AdminProfileSerializer(profile).data
        except Profile.DoesNotExist:
            return None

