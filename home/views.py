from django.shortcuts import render
from users.models import ManpowerProfile
from django.contrib.auth.models import User
from  django.views.generic.list import ListView

# Create your views here.
def home(request):
    return render(request , 'home/index.html')

class professionals_list(ListView):
   model = ManpowerProfile
   template_name = "home/index.html"
   context_object_name = "ManpowerList"

   def get_queryset(self):
        return ManpowerProfile.objects.select_related('user')