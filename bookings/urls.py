from django.contrib import admin
from django.urls  import path
from . import views
app_name = 'bookings'
urlpatterns = [
   
    path('', views.bookings, name = 'bookings'),
    path('booking-form/<int:professional_id>/', views.booking_form, name='booking_form'),

    path('checkout/<int:booking_id>/', views.checkout, name='checkout'),
    path('esewa-callback/', views.esewa_callback, name='esewa_callback'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),



]