
# users/views.py
from datetime import datetime, date
import re
# At the top of views.py
from django.utils import timezone
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login as auth_login ,get_user_model
from django.db import transaction                                                           
from .forms import ManpowerProfileUpdateForm, UserProfileUpdateForm, UserSignupForm, LoginForm, ManpowerSignupForm
from users.models import  ManpowerProfile, District, Municipality, Province
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth import authenticate, login as auth_login   
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from bookings.models import Booking, Payment    


@login_required
def update_profile(request):
    """Handle profile update for both client and professional."""
    user = request.user
    manpower_profile = None
    if user.is_professional:
        manpower_profile = get_object_or_404(ManpowerProfile, user=user)

    if request.method == "POST":
        user_form = UserProfileUpdateForm(request.POST, instance=user)
        profile_form = ManpowerProfileUpdateForm(request.POST, request.FILES, instance=manpower_profile) if manpower_profile else None

        if user_form.is_valid() and (not profile_form or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("users:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserProfileUpdateForm(instance=user)
        profile_form = ManpowerProfileUpdateForm(instance=manpower_profile) if manpower_profile else None

    return render(request, "users/update_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })


@login_required
def toggle_availability(request, pk):
    """Toggle availability for professionals only."""
    if request.method == "POST":
        manpower = get_object_or_404(ManpowerProfile, pk=pk, user=request.user)
        manpower.is_available = not manpower.is_available
        manpower.save()
        return JsonResponse({"success": True, "is_available": manpower.is_available})
    return JsonResponse({"success": False}, status=400)

User = get_user_model()
def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit= False)
            # user.username = form.cleaned_data['email'].split('@')[0]+ str(User.objects.count()
            phone = form.cleaned_data['phone_number']
            pattern = r'^98\d{8}$'
            if not re.match(pattern, str(phone)):
                raise ValueError("Phone number must be 10 digits and start with '98'.")
            
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('users:login')
    else:
        form = UserSignupForm()
    return render(request, 'users/signup.html', {'form': form})

@login_required
def professional_signup(request):
    if request.method == 'POST':
        form = ManpowerSignupForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            manpower_profile = form.save(commit=False)
            manpower_profile.user = request.user
            request.user.is_professional = True
            request.user.save()
            manpower_profile.save()
            messages.success(request, "Profile created successfully.")
            return redirect('users:profile')  # Adjust to your profile URL
        else:
            messages.error(request, "Please correct the errors below.")
            print(form.errors)
    else:
        form = ManpowerSignupForm(user=request.user)
    return render(request, 'users/professional_signup.html', {'form': form})


# @login_required
# def profile_update(request):
#     user = request.user
#     # profile_type = request.GET.get.is_client  # Default to user profile
    
#     try:
#         # Determine which profile to update
#         if profile_type == 
#             profile = ManpowerProfile.objects.get(user=user)
#             form_class = ManpowerProfileUpdateForm
#             # success_url = reverse('users:manpower_profile')
#         else:
#             profile = user
#             form_class = UserProfileUpdateForm
        
#         success_url = reverse('users:profile')
#         if request.method == 'POST':
#             form = form_class(request.POST, request.FILES, instance=profile)
#             if form.is_valid():
#                 form.save()
                
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': True,
#                         'message': "Profile updated successfully."
#                     })
#                 messages.success(request, "Profile updated successfully.")
#                 return redirect(success_url)
#         else:
#             form = form_class(instance=profile)
            
#         # For AJAX requests, return just the form HTML
#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return render(request, 'users/profile.html', {'form': form})
            
#         return render(request, 'users/profile.html', {'form': form})
        
#     except (ManpowerProfile.DoesNotExist, CustomUser.DoesNotExist):
#         raise Http404("Profile not found")

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data.get('phone_number')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=phone, password=password)
            if user:
                auth_login(request, user)
                next_page = request.POST.get('next') or request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('home_module:home')
            else:
                form.add_error(None, 'Invalid phone number or password')
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')  # Redirect to login page after logout

    def post(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().post(request, *args, **kwargs)


def get_districts(request):
    province_name = request.GET.get('province_name', '')
    districts = []
    if province_name:
        province = Province.objects.filter(name=province_name).first()
        if province:
            districts = list(District.objects.filter(province=province).values('name'))
            districts = [{'name': d['name']} for d in districts]
    return JsonResponse({'districts': districts})

def get_municipality(request):
    district_name = request.GET.get('district_name', '')
    municipalities = []
    if district_name:
        municipalities = list(Municipality.objects.filter(district__name=district_name).values('name'))
        municipalities = [{'name': m['name']} for m in municipalities]
    return JsonResponse({'municipality': municipalities})

def get_wards(request):
    municipality_name = request.GET.get('municipality_name', '')
    try:
        municipality = Municipality.objects.get(name=municipality_name)
        wards = list(range(1, municipality.ward + 1))
        return JsonResponse({'wards': wards})
    except Municipality.DoesNotExist:
        return JsonResponse({'wards': []})

@login_required             
def profile(request):
    user = request.user
    
    # Check if user is a professional
    try:
        pro = ManpowerProfile.objects.get(user=user)
        is_professional = True
        manpower_profile = pro
        
        # Calculate stats for professionals
        now = datetime.now()
        
        # 1. Upcoming Bookings count
        upcoming_count = pro.professional_bookings.filter(
            booking_time__gt=now,
            status__in=["upcoming", "ongoing"]
        ).count()
        
        # 2. Average Rating
        reviews = pro.reviews_received.all()
        total_reviews = reviews.count()
        
        if total_reviews > 0:
            avg_rating = sum(r.rating for r in reviews) / total_reviews
            avg_rating = round(avg_rating, 1)
        else:
            avg_rating = 0
        
        # 3. Reviews count
        reviews_count = total_reviews
        
    except ManpowerProfile.DoesNotExist:
        # User is not a professional
        pro = None
        manpower_profile = None
        is_professional = False
        upcoming_count = 0
        avg_rating = 0
        reviews_count = 0
    
    # Forms for profile editing
    user_form = UserProfileUpdateForm(instance=user)
    profile_form = ManpowerProfileUpdateForm(instance=manpower_profile) if manpower_profile else None
    
    context = {
        "user": user,
        "user_profile": user,  # Keep both for compatibility
        "manpower_profile": manpower_profile,
        "pro": pro,  # Same as manpower_profile
        "is_professional": is_professional,
        "user_form": user_form,
        "profile_form": profile_form,
        # Stats for professionals
        "upcoming_count": upcoming_count,
        "avg_rating": avg_rating,
        "reviews_count": reviews_count,
    }
    
    return render(request, "users/profile.html", context)

@login_required
def prof_dashboard(request):
    pro = get_object_or_404(ManpowerProfile, user=request.user)
    
    # ✅ Use timezone.now() instead of datetime.now()
    now_utc = timezone.now()  # Timezone-aware UTC datetime
    
    
    # 1. TODAY'S BOOKINGS: Bookings happening TODAY in UTC
    today_bookings = pro.professional_bookings.filter(
        booking_time__date=now_utc.date(),  # Compare UTC dates
        status__in=["upcoming", "ongoing"]
    ).order_by('booking_time')
    
    # 2. UPCOMING BOOKINGS: Bookings in the FUTURE (UTC comparison)
    upcoming_bookings = pro.professional_bookings.filter(
        booking_time__gt=now_utc,  # Compare UTC datetime with UTC
        status__in=["upcoming", "ongoing"]
    ).order_by('booking_time')
    
    # 3. HISTORY: Past bookings (before now in UTC)
    history = pro.professional_bookings.filter(
        booking_time__lt=now_utc  # Compare UTC datetime with UTC
    ).exclude(
        booking_time__date=now_utc.date(),  # Exclude today's bookings,
        status__in=["upcoming", "ongoing"]
    ).order_by('-booking_time')
    
    reviews = pro.reviews_received.all()
    total_reviews = reviews.count()
    
    # Calculate average rating
    if total_reviews > 0:
        avg_rating = sum(r.rating for r in reviews) / total_reviews
        avg_rating = round(avg_rating, 1)
    else:
        avg_rating = 0
    
    # Calculate rating breakdown
    rating_breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        rating = int(r.rating)
        if rating in rating_breakdown:
            rating_breakdown[rating] += 1
    
    # Get latest review
    latest_review = reviews.order_by('-created_at').first()
    
    for booking in list(today_bookings) + list(upcoming_bookings) + list(history):
        if booking.booking_time < now_utc:
            booking.status = 'completed'
        else:
            booking.status = 'upcoming'

      # Payment info
        try:
            booking.payment
        except Payment.DoesNotExist:
            booking.payment = None
        
        booking.remaining_balance = booking.total_fee - booking.deposit_amount
    context = {
        "pro": pro,
        "today_bookings": today_bookings,
        "upcoming_bookings": upcoming_bookings,
        "history": history,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "rating_breakdown": rating_breakdown,
        "total_reviews": total_reviews,
        "latest_review": latest_review,
       
    }
    
    return render(request, "users/professional_dashboard.html", context)

def view_booking_route(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    pro = booking.professional
    
    # Debug print
    print(f"DEBUG - Booking ID: {booking_id}")
    print(f"DEBUG - Professional: {pro.user.full_name}")
    print(f"DEBUG - Pro coordinates: {pro.latitude}, {pro.longitude}")
    print(f"DEBUG - Customer coordinates: {booking.user_latitude}, {booking.user_longitude}")
    print(f"DEBUG - Pro coordinates exist: {pro.latitude is not None}, {pro.longitude is not None}")
    print(f"DEBUG - Customer coordinates exist: {booking.user_latitude is not None}, {booking.user_longitude is not None}")
    
    context = {
        'booking': booking,
        'pro': pro,
        # Pass coordinates as separate variables too
        'pro_lat': pro.latitude or 0,
        'pro_lng': pro.longitude or 0,
        'cus_lat': booking.user_latitude or 0,
        'cus_lng': booking.user_longitude or 0,
    }
  
  
    return render(request, 'users/view_route.html', context)



@login_required
@require_POST
def mark_booking_completed(request, booking_id):
    """Mark a booking as completed (set end_time = now, status = completed)"""
    try:
        # Get the booking
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verify this professional owns the booking
        if booking.professional.user != request.user:
            return JsonResponse({
                'success': False, 
                'message': 'You do not have permission to complete this booking'
            }, status=403)
        
        # Check if booking can be completed
        now_utc = timezone.now()
        
        # Allow completion if booking is upcoming or ongoing
        if booking.status not in ['upcoming', 'ongoing']:
            return JsonResponse({
                'success': False, 
                'message': f'Cannot complete a {booking.status} booking'
            })
        if booking.booking_time > now_utc:
            return JsonResponse({
                'success': False,
                'message': 'Cannot complete booking before its start time'
            })
    # Update the booking
        booking.end_time = now_utc
        booking.status = 'completed'
        booking.save()
        
        # Optional: Create a completion record or log
        
        return JsonResponse({
            'success': True,
            'message': 'Booking marked as completed successfully',
            'booking_id': booking.id,
            'completed_time': now_utc.isoformat(),
            'new_status': booking.status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        }, status=500)


def terms_and_conditions(request):
    return render(request, "users/terms.html")

# Django caching example
from django.core.cache import cache
import hashlib
import requests

def call_openrouteservice_api(pro_lat, pro_lng, cus_lat, cus_lng):
    """Call OpenRouteService API to get route data between two coordinates."""
    try:
        api_key = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjNiMzFlMDA4NTA3NzQ3ZTM5MTBiZTZiNzBiZDNmYmQ0IiwiaCI6Im11cm11cjY0In0="  # Replace with your actual API key
        url = f"https://api.openrouteservice.org/v2/directions/driving?api_key={api_key}&start={pro_lng},{pro_lat}&end={cus_lng},{cus_lat}"
        
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Failed to fetch route data"}
    except Exception as e:
        return {"error": str(e)}

@login_required
def get_route(request):
    pro_lat = request.GET.get('pro_lat')
    pro_lng = request.GET.get('pro_lng')
    cus_lat = request.GET.get('cus_lat')
    cus_lng = request.GET.get('cus_lng')
    
    # Create cache key
    cache_key = hashlib.md5(f"{pro_lat},{pro_lng},{cus_lat},{cus_lng}".encode()).hexdigest()
    
    # Check cache first
    cached_route = cache.get(cache_key)
    if cached_route:
        return JsonResponse(cached_route)
    
    # Call API if not cached
    route_data = call_openrouteservice_api(pro_lat, pro_lng, cus_lat, cus_lng)
    
    # Cache for 24 hours
    cache.set(cache_key, route_data, 60*60*24)
    
    return JsonResponse(route_data)