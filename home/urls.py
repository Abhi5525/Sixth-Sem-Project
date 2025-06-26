from django.contrib import admin
from django.urls  import path
from . import views


app_name = 'home_module'
urlpatterns = [
    path('', views.home , name = 'home' ),
    path('api/manpower/', views.manpower_list_api, name='manpower_list_api'),
     path('api/manpower/<int:pk>/', views.manpower_detail_api, name='manpower-detail'),
    # path('professionals', views.professionals_list, name = "professionals_List")
    # path('bookings/', views.bookings, name = 'bookings'),
    # path('profile/', views.profile, name = 'profile'),


]