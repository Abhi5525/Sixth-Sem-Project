from django.db import models
from django.core.validators import RegexValidator
import re
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
# Custom User Manager (unchanged)
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number=None, full_name=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required for normal users.')
        if not full_name:
            raise ValueError('Full name is required for normal users.')
        if not password:
            raise ValueError('Password is required.')

        user = self.model(
            phone_number=phone_number,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        if not password:
            raise ValueError('Password is required.')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

# Custom User Model (with added user_type and location)
class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('professional', 'Professional'),
    )
    phone_number = models.CharField(max_length=10, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_client = models.BooleanField(default=True)
    is_professional = models.BooleanField(default=False)

   
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def check_phone_number(self):
        if not self.phone_number:
            raise ValueError("Phone number is required.")
        # must be exactly 10 digits and start with '98'
        pattern = r'^98\d{8}$'
        if not re.match(pattern, str(self.phone_number)):
            raise ValueError("Phone number must be 10 digits and start with '98'.")
    
    def __str__(self):
        return self.full_name or self.phone_number

# Skill Model
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, default="General", choices=[
        ('Plumbing', 'Plumbing'),
        ('Electrical', 'Electrical'),
        ('Carpentry', 'Carpentry'),
        ('Cleaning', 'Cleaning'),
        ('Painting', 'Painting'),
        ('Masonry', 'Masonry'),
        ('General', 'General'),
        ('Other', 'Other'),
    ])
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

# Manpower Profile (with GPS and availability)
class ManpowerProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    email = models.EmailField(unique=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    skill = models.CharField(max_length=100, null=True, blank=True)  # Deprecated: Use 'skills' ManyToMany instead
    skills = models.ManyToManyField(Skill, blank=True, related_name='professionals')  # New: Multiple skills
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100, default="Kathmandu")
    municipality = models.CharField(max_length=100)
    ward = models.IntegerField()
    experience = models.IntegerField(default=0)
    about_yourself = models.TextField(blank=True, null=True)
    citizenship_front = models.ImageField(upload_to='manpower/citizenship/front/', blank=True, null=True)
    citizenship_back = models.ImageField(upload_to='manpower/citizenship/back/', blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Changed to DecimalField for precision
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.IntegerField(default=0)

    profile_picture = models.ImageField(upload_to='manpower/profile_pictures/', blank=True, null=True, default='manpower/profile_pictures/images.png')
    is_available = models.BooleanField(default=True)  # Availability status
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Verification fields
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_professionals')
    rejection_reason = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.user.full_name}'s Manpower Profile"

    def save(self, *args, **kwargs):
        # Only validate if this is a new save or rate/experience changed
        if not self.pk or 'update_fields' not in kwargs:
            self.check_rate()
        super().save(*args, **kwargs)

    def check_rate(self):
        if self.experience < 1:
            if not (0 <= self.rate <= 200):
                raise ValueError("Rate must be between 0 and 200 for experience less than 1 year.")
        elif 1 <= self.experience < 3:
            if not (0 <= self.rate <= 300):
                raise ValueError("Rate must be between 0 and 300 for experience between 1 and 3 years.")
        elif 3 <= self.experience < 5:
            if not (0 <= self.rate <= 400):
                raise ValueError("Rate must be between 0 and 400 for experience between 3 and 5 years.")
        else:
            if not (0 <= self.rate <= 600):
                raise ValueError("Rate must be between 0 and 600 for experience 5 years or more.")
    

class Province(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class District(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete= models.CASCADE, related_name="districts")

    def __str__(self):
        return self.name
    

class Municipality(models.Model):
    name = models.CharField(max_length=100)
    ward = models.IntegerField(default=35)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="municipality")


    def __str__(self):
        return self.name