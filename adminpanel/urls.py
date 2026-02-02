from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('pending/', views.pending_verifications, name='pending_verifications'),
    path('professionals/', views.all_professionals, name='all_professionals'),
    path('professionals/<int:pk>/', views.professional_detail, name='professional_detail'),
    path('professionals/<int:pk>/approve/', views.approve_professional, name='approve_professional'),
    path('professionals/<int:pk>/reject/', views.reject_professional, name='reject_professional'),
    path('professionals/<int:pk>/toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('bookings/', views.all_bookings, name='all_bookings'),
]
