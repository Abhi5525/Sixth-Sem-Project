
# users/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    

    def __str__(self):
        return self.full_name

class ManpowerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # name = models.CharField(max_length=100)
    address = models.TextField()
    # phone = models.CharField(max_length=15)
    skill = models.CharField(max_length=100)
    experience = models.CharField(max_length=200)
    # photo = models.ImageField(upload_to='manpower/photos/', blank=True, null=True)
    citizenship_front = models.ImageField(upload_to='manpower/citizenship/front/', blank=True, null=True)
    citizenship_back = models.ImageField(upload_to='manpower/citizenship/back/', blank=True, null=True)

    def __str__(self):
        return self()
    

class Province(models.Model):
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
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="municipality")

    def __str__(self):
        return self.name
    
class Ward(models.Model):
    number = models.PositiveBigIntegerField()
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name="ward")

    def __str__(self):
        return f"Ward no - {self.number}"