from django.contrib import admin
from django.urls  import path
from users import views
# from .views import CustomLoginView

app_name = 'users'
urlpatterns = [
    path('profile/', views.profile, name = 'profile'),
    path('login/', views.login, name='login'),
    # path('userlist', views.user_list, name='user_list'),
    path('signup/', views.signup, name='signup'),
    path('signup/professional/', views.professional_signup, name='professional_signup'),

]