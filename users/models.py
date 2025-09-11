from django.db import models
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
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_client = models.BooleanField(default=True)
    is_professional = models.BooleanField(default=False)

   
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email or self.phone_number

# Manpower Profile (with GPS and availability)
class ManpowerProfile(models.Model):
    email = models.EmailField(unique=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    skill = models.CharField(max_length=100)  # e.g., "Plumber", "Carpenter"
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100, default="Kathmandu")
    municipality = models.CharField(max_length=100)
    ward = models.IntegerField()
    experience = models.CharField(max_length=200, default="no experience")
    citizenship_front = models.ImageField(upload_to='manpower/citizenship/front/', blank=True, null=True)
    citizenship_back = models.ImageField(upload_to='manpower/citizenship/back/', blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Changed to DecimalField for precision
    profile_picture = models.ImageField(upload_to='manpower/profile_pictures/', blank=True, null=True, default='manpower/profile_pictures/images.png')
    is_available = models.BooleanField(default=True)  # Availability status
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return f"{self.user.full_name}'s Manpower Profile"
    

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
    
# class Ward(models.Model):
#     number = models.PositiveSmallIntegerField()
#     municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="ward")

#     def __str__(self):
#         return f"Ward no - {self.number}"