from django.contrib import admin
from django.urls  import path
from bookings import views
app_name = 'bookings'
urlpatterns = [
   
    path('bookings', views.bookings, name = 'bookings'),


]