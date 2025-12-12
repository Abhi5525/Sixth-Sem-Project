from django.contrib import admin
from django.urls  import path
from . import views


app_name = 'home_module'
urlpatterns = [
    path('', views.home , name = 'home' ),
    path('maps/', views.maps, name='maps'),
    path('api/manpower/', views.manpower_list_api, name='manpower_list_api'),
     path('api/manpower/<int:pk>/', views.manpower_detail_api, name='manpower-detail'),
     path('api/updatelocation/', views.update_professional_location, name='update_location'),
    # path('find-professionals/', views.find_professionals, name='find_professionals'),
   path('review/<int:professional_id>/', views.submit_review, name='submit_review'),
    path('review-page/<int:professional_id>/', views.review_page, name='review_page'),
    path('api/availability/', views.professional_availability, name='professional_availability'),


    # path('professionals', views.professionals_list, name = "professionals_List")
    # path('bookings/', views.bookings, name = 'bookings'),
    # path('profile/', views.profile, name = 'profile'),


]