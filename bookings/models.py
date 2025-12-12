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
    status = models.CharField(
        max_length=20,
        choices=[("upcoming", "Upcoming"), ("ongoing", "Ongoing"), ("completed", "Completed")],
        default="upcoming"
    )
    
    @property
    def remaining_payment(self):
        return self.total_fee - self.deposit_amount
    

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def clean(self):
        # Check 1: Verify professional exists (better check)
        if not hasattr(self.professional, 'user'):
            raise ValidationError("Selected user does not have a professional profile.")
        
        # OR check if user has ManpowerProfile
        if not hasattr(self.professional.user, 'manpower_profile'):
            raise ValidationError("Selected user is not registered as a professional.")
        
        # Check 2: Duration validation
        if self.duration_hours <= 0:
            raise ValidationError("Duration must be positive.")
        
        # Check 3: Overlapping bookings with timezone awareness
        if self.professional and self.booking_time:
            # Ensure times are timezone-aware
            if not timezone.is_aware(self.booking_time):
                self.booking_time = timezone.make_aware(self.booking_time, timezone=timezone.utc)
            
            # Calculate end time
            end_time = self.booking_time + timezone.timedelta(hours=self.duration_hours)
            
            # Check for overlapping bookings (using UTC times)
            overlapping_bookings = Booking.objects.filter(
                professional=self.professional,
                booking_time__lt=end_time,
                end_time__gt=self.booking_time
            ).exclude(pk=self.pk)
            
            if overlapping_bookings.exists():
                raise ValidationError(
                    f"{self.professional.user.full_name} is already booked for this time slot."
                )
        
        # Check 4: Minimum 1 hour advance booking
        if self.booking_time:
            # Get current time in UTC
            now_utc = timezone.now()
            
            # Ensure booking_time is timezone-aware
            if not timezone.is_aware(self.booking_time):
                self.booking_time = timezone.make_aware(self.booking_time, timezone=timezone.utc)
            
            # Calculate minimum allowed booking time (1 hour from now)
            min_booking_time = now_utc + timezone.timedelta(hours=1)
            
            if self.booking_time < min_booking_time:
                # Convert to local time for error message
                user_tz = timezone.get_current_timezone()
                local_min_time = timezone.localtime(min_booking_time, user_tz)
                raise ValidationError(
                    f"Bookings must be made at least 1 hour in advance. "
                    f"Earliest available time is {local_min_time.strftime('%Y-%m-%d %I:%M %p')}"
                )

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
