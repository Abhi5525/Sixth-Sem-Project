from django.contrib import admin
from django.urls  import path
from users import views
from .views import CustomLoginView

app_name = 'users'
urlpatterns = [
    path('profile/', views.profile, name = 'profile'),
   path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.signup_choice, name='signup'),
    path('signup/user/', views.user_signup, name='user_signup'),
    path('signup/professional/', views.professional_signup, name='professional_signup'),

]