from decimal import Decimal
from django.db import models

from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
import re
from datetime import timedelta, timezone as dt_timezone
from users.models import CustomUser , ManpowerProfile # Import CustomUser from users app

BOOKING_PHONE_PATTERN = re.compile(r"^98\d{8}$")
BOOKING_GAP_MINUTES = 30

class Booking(models.Model):
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='client_bookings')
    client_name = models.CharField(max_length=100, blank=True)  # New field
    client_phone = models.CharField(max_length=10, blank=True)
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
        # Check 1: Verify professional is selected
        if not self.professional:
            raise ValidationError("Professional must be selected.")
        
        # Check 2: Verify professional is approved and available for booking
        if not self.professional.user:
            raise ValidationError("Selected professional does not have a user account.")
        
        if self.professional.verification_status != 'APPROVED':
            raise ValidationError("Selected professional is not approved for bookings. Only APPROVED professionals can be booked.")
        
        if not self.professional.user.is_professional:
            raise ValidationError("Selected user is not registered as a professional.")
        
        if not self.professional.is_available:
            raise ValidationError(f"{self.professional.user.full_name} is currently unavailable for bookings.")
        
        # Check 3: Duration validation
        if self.duration_hours < 0.5 or self.duration_hours > 24:
            raise ValidationError("Duration must be between 0.5 and 24 hours.")

        # Check 3.1: Client phone validation
        if not self.client_phone:
            raise ValidationError("Phone number is required.")
        normalized_phone = str(self.client_phone).strip()
        if not BOOKING_PHONE_PATTERN.fullmatch(normalized_phone):
            raise ValidationError("Phone number must be 10 digits and start with 98.")
        self.client_phone = normalized_phone
        
        # Check 3: Overlapping bookings with timezone awareness
        if self.professional and self.booking_time:
            # Ensure times are timezone-aware
            if not timezone.is_aware(self.booking_time):
                self.booking_time = timezone.make_aware(self.booking_time, timezone=dt_timezone.utc)
            
            # Calculate end time
            end_time = self.booking_time + timedelta(hours=self.duration_hours)
            
            # Check for conflicts, including a 30-minute gap after each existing booking.
            existing_bookings = Booking.objects.filter(
                professional=self.professional,
            ).exclude(pk=self.pk)

            for existing in existing_bookings:
                existing_end = existing.end_time
                if existing_end is None and existing.booking_time and existing.duration_hours:
                    existing_end = existing.booking_time + timedelta(hours=existing.duration_hours)
                if existing_end is None:
                    continue

                buffered_end = existing_end + timedelta(minutes=BOOKING_GAP_MINUTES)
                if self.booking_time < buffered_end and end_time > existing.booking_time:
                    raise ValidationError(
                        f"{self.professional.user.full_name} is already booked for this time slot."
                    )
        
        # Check 4: Minimum 30 minutes advance booking
        if self.booking_time:
            # Get current time in UTC
            now_utc = timezone.now()
            
            # Ensure booking_time is timezone-aware
            if not timezone.is_aware(self.booking_time):
                self.booking_time = timezone.make_aware(self.booking_time, timezone=dt_timezone.utc)
            
            # Calculate minimum allowed booking time (30 minutes from now)
            min_booking_time = now_utc + timedelta(hours=0.5)
            
            if self.booking_time < min_booking_time:
                # Convert to local time for error message
                user_tz = timezone.get_current_timezone()
                local_min_time = timezone.localtime(min_booking_time, user_tz)
                raise ValidationError(
                    f"Bookings must be made at least 30 mins in advance. "
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
