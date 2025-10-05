from decimal import Decimal
from django.db import models

from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from users.models import CustomUser , ManpowerProfile # Import CustomUser from users app

class Booking(models.Model):
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_bookings')
    client_name = models.CharField(max_length=100, blank=True)  # New field
    professional = models.ForeignKey(ManpowerProfile, on_delete=models.CASCADE, related_name='professional_bookings')
    booking_time = models.DateTimeField()  # Start time of the service
    duration_hours = models.FloatField()  # Duration in hours
    end_time = models.DateTimeField(null=True, blank=True)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)  # Total fee
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2)  # 10% deposit
    is_confirmed = models.BooleanField(default=False)  # Confirmed after payment
    created_at = models.DateTimeField(auto_now_add=True)
    user_latitude = models.FloatField(null=True, blank=True)
    user_longitude = models.FloatField(null=True, blank=True)
    professional_latitude = models.FloatField(null=True, blank=True)
    professional_longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def clean(self):
        if not self.professional.user.is_professional:
            raise ValidationError("Selected user is not a professional.")
        if self.professional and self.booking_time:
            if self.duration_hours <= 0:
                raise ValidationError("Duration must be positive.")
            end_time = self.booking_time + timezone.timedelta(hours=self.duration_hours)
            overlapping_bookings = Booking.objects.filter(
                professional=self.professional,
                booking_time__lt=end_time,
                booking_time__gte=self.booking_time
            ).exclude(pk=self.pk)
            if overlapping_bookings.exists():
                raise ValidationError(f"{self.professional.user.full_name} is already booked for this time slot.")

    def save(self, *args, **kwargs):
        self.clean()  # Validate first
        try:
            self.professional_latitude = self.professional.latitude
            self.professional_longitude = self.professional.longitude
            if not self.total_fee:
                self.total_fee = Decimal(str(self.professional.rate)) * Decimal(str(self.duration_hours))
            if not self.deposit_amount:
                self.deposit_amount = self.total_fee * Decimal('0.1')  # 10% deposit
        except (AttributeError, ValueError, TypeError) as e:
            raise ValidationError("Invalid data for fee calculation or missing profile fields.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} by {self.client.full_name} for {self.professional.user.full_name}"
        

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    transaction_uuid = models.UUIDField(default=uuid.uuid4, unique=True)  # Unique ID for eSewa
    esewa_order_id = models.CharField(max_length=50, unique=True, null=True)  # eSewa order ID
    esewa_ref_id = models.CharField(max_length=50, null=True, blank=True)  # eSewa transaction reference ID
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Paid amount (10% deposit)
    is_paid = models.BooleanField(default=False)  # Payment status
    payment_date = models.DateTimeField(null=True, blank=True)  # Date of payment
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Booking {self.booking.id} - {'Paid' if self.is_paid else 'Pending'}"
    
# bookings/models.py

class RatingReview(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews_given")
    professional = models.ForeignKey(ManpowerProfile, on_delete=models.CASCADE, related_name="reviews_received")
    
    rating = models.PositiveSmallIntegerField(default=0)  # 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.full_name} → {self.professional.user.full_name} ({self.rating}⭐)"
