from django.contrib import admin
from django.urls  import path
from . import views

app_name = 'home_module'
urlpatterns = [
    path('', views.home , name = 'home' ),
    # path('bookings/', views.bookings, name = 'bookings'),
    # path('profile/', views.profile, name = 'profile'),


]