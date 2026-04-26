from  rest_framework import serializers
from users.models import CustomUser, ManpowerProfile

class ManpowerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.full_name')
    user_id = serializers.IntegerField(source='user.id')
    location = serializers.SerializerMethodField()
    rate = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    about = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = ManpowerProfile
        fields = ['id','user_id', 'name',  'location', 'rate', 'experience', 'about', 'profile_picture','total_reviews','average_rating']

    def get_location(self, obj):
        return f"{obj.province}, {obj.district}"

    def get_rate(self, obj):
        return f"{obj.rate} Rs per hour"

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else "https://via.placeholder.com/100"

    def get_about(self, obj):
        return f"{obj.about_yourself}" if obj.about_yourself else "I am a professional manpower registered to Mistri Nepal."

    def get_total_reviews(self, obj):
        return obj.reviews_received.count()

    def get_average_rating(self, obj):
        reviews = obj.reviews_received.all()
        total_reviews = reviews.count()
        if total_reviews == 0:
            return 0
        return round(sum(review.rating for review in reviews) / total_reviews, 1)
