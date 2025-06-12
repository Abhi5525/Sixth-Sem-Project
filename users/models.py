
# users/models.py
from django.db import models
from django.contrib.auth.models import User
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    
    def __str__(self):
        return self.username

class ManpowerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    skill = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100, default="kathmandu")
    municipality = models.CharField(max_length=100)
    ward = models.IntegerField()
    experience = models.CharField(max_length=200, default="no experience")
    citizenship_front = models.ImageField(upload_to='manpower/citizenship/front/', blank=True, null=True)
    citizenship_back = models.ImageField(upload_to='manpower/citizenship/back/', blank=True, null=True)

    def __str__(self):
        return self.full_name  # or self.user.username

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