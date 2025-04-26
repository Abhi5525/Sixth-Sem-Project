from django.contrib import admin
from django.urls  import path
from bookings import views
app_name = 'bookings'
urlpatterns = [
   
    path('', views.bookings, name = 'bookings'),


]