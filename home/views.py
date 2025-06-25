from django.shortcuts import render
from users.models import ManpowerProfile
# from django.contrib.auth.models import User
from  django.views.generic.list import ListView

# Create your views here.
def home(request):
     manpower_list = ManpowerProfile.objects.all()
     return render(request, 'home/index.html', {
        'ManpowerList': manpower_list
    })
   
