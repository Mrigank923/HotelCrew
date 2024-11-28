from rest_framework import serializers


class DailyHotelPerformanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    performance_percentage = serializers.FloatField()


class WeeklyHotelPerformanceSerializer(serializers.Serializer):
    week_range = serializers.CharField()
    weekly_stats = DailyHotelPerformanceSerializer(many=True)


class DailyStaffPerformanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    performance_percentage = serializers.FloatField()

class WeeklyStaffPerformanceSerializer(serializers.Serializer):
    week_range = serializers.CharField()
    daily_stats = DailyStaffPerformanceSerializer(many=True)


class DailyFinanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_revenue = serializers.FloatField()

class WeeklyFinanceSerializer(serializers.Serializer):
    week_range = serializers.CharField()
    daily_stats = DailyFinanceSerializer(many=True)
