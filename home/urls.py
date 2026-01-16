from django.contrib import admin
from django.urls  import path
from . import views
from django.views.generic.base import RedirectView
from django.conf.urls.static import static

app_name = 'home_module'
urlpatterns = [
    path('', views.home , name = 'home' ),
    path('maps/', views.maps, name='maps'),
    path('api/manpower/', views.manpower_list_api, name='manpower_list_api'),
     path('api/manpower/<int:pk>/', views.manpower_detail_api, name='manpower-detail'),
     path('api/updatelocation/', views.update_professional_location, name='update_location'),
     path('api/availability/', views.professional_availability, name='professional_availability'),

    
   path('review/<int:professional_id>/', views.submit_review, name='submit_review'),
    path('review-page/<int:professional_id>/', views.review_page, name='review_page'),
    
    path('save-user-location/', views.save_user_location, name='save_user_location'),


 path(
        "favicon.ico",
        RedirectView.as_view(
            url="/static/home/favicon.ico",
            permanent=True
        ),
    ),
]