from django.contrib import admin
from .models import UserProfile, ManpowerProfile,Province,District,Municipality,Ward

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(ManpowerProfile)
admin.site.register(Province)
admin.site.register(District)
admin.site.register(Municipality)
admin.site.register(Ward)
