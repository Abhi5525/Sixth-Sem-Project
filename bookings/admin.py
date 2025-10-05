from django.contrib import admin
from .models import Booking
from .models import Payment , RatingReview
# Register your models here.
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(RatingReview)