from django.contrib import admin
from django.urls  import path
from users import views
from .views import CustomLoginView

app_name = 'users'
urlpatterns = [
    path('', views.profile, name = 'profile'),
   path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup_choice, name='signup_choice'),
    path('signup/user/', views.user_signup, name='user_signup'),
    path('signup/manpower/', views.manpower_signup, name='manpower_signup'),

]