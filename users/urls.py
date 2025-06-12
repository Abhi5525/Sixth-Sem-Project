from django.contrib import admin
from django.urls  import path
from . import views
from django.contrib.auth.views import LogoutView

# from .views import CustomLoginView

app_name = 'users'
urlpatterns = [
    path('profile/', views.profile, name = 'profile'),
    path('login/', views.login, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    # path('userlist', views.user_list, name='user_list'),
    path('signup/', views.signup, name='signup'),
    path('signup/professional/', views.professional_signup, name='professional_signup'),


    path('municipality/<int:district_id>/', views.get_municipality, name = "get_municipality"),
    path('district/<int:province_id>/', views.get_districts, name="get_districts"),
    path('ward/<int:municipality_id>/', views.get_wards, name = "get_ward"),
]
