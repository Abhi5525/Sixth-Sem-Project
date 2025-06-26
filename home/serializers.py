from  rest_framework import serializers
from users.models import CustomUser, ManpowerProfile

class ManpowerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.full_name')
    location = serializers.SerializerMethodField()
    rate = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    about = serializers.SerializerMethodField()

    class Meta:
        model = ManpowerProfile
        fields = ['id', 'name',  'location', 'rate', 'experience', 'about', 'profile_picture']

    def get_location(self, obj):
        return f"{obj.province}, {obj.district}"

    def get_rate(self, obj):
        return f"{obj.rate} Rs per hour"

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else "https://via.placeholder.com/100"

    def get_about(self, obj):
        return f"Experienced professional specializing in {obj.skill}. Committed to providing high-quality services."
