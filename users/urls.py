from django.contrib import admin
from django.urls  import path
from . import views
from django.contrib.auth.views import LogoutView

from rest_framework_simplejwt.views import (
    
    TokenRefreshView,
)
from .tokens import CustomTokenObtainPairView


app_name = 'users'
urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('signup/professional/', views.professional_signup, name='professional_signup'),

    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/toggle-availability/<int:pk>/', views.toggle_availability, name='toggle_availability'),
    path('profile/', views.profile, name='profile'),
    path("profile/update/", views.update_profile, name="update_profile"),

    
    # URL to handle client profile updates
   
    path('district/', views.get_districts, name="get_districts"),  # Changed to handle GET param
    path('municipality/', views.get_municipality, name="get_municipality"),
    path('ward/', views.get_wards, name="get_ward"),
]
