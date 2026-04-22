
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
        
        # Check if professional account is rejected
        if manpower_profile.verification_status == 'REJECTED':
            messages.error(request, "Your professional account has been rejected. You cannot update your professional profile. Please contact support.")
            return redirect("users:profile")

    if request.method == "POST":
        # For PENDING professionals, allow update but show warning
        if manpower_profile and manpower_profile.verification_status == 'PENDING':
            messages.warning(request, "Your changes will be saved, but your profile will only be visible to clients after admin approval.")
        
        # For REJECTED professionals, allow update to fix issues
        if manpower_profile and manpower_profile.verification_status == 'REJECTED':
            messages.info(request, "Please fix the issues mentioned in the rejection reason. After saving, you can request re-verification.")
        
        user_form = UserProfileUpdateForm(request.POST, instance=user)
        profile_form = ManpowerProfileUpdateForm(request.POST, request.FILES, instance=manpower_profile) if manpower_profile else None

        if user_form.is_valid() and (not profile_form or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully!'
                })
            
            messages.success(request, "Profile updated successfully.")
            return redirect("users:profile")
        else:
            # Combine errors from both forms
            errors = {}
            if user_form.errors:
                errors.update(user_form.errors)
            if profile_form and profile_form.errors:
                errors.update(profile_form.errors)
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                    'message': 'Please correct the errors below.'
                }, status=400)
            
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserProfileUpdateForm(instance=user)
        profile_form = ManpowerProfileUpdateForm(instance=manpower_profile) if manpower_profile else None

    # For non-AJAX requests, render the template
    return render(request, "users/update_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "verification_status": manpower_profile.verification_status if manpower_profile else None,
    })


@login_required
def toggle_availability(request, pk):
    """Toggle availability for professionals only."""
    if request.method == "POST":
        manpower = get_object_or_404(ManpowerProfile, pk=pk, user=request.user)
        
        # Check verification status
        if manpower.verification_status == 'PENDING':
            return JsonResponse({
                "success": False,
                "message": "You can toggle availability only after your account is approved by admin."
            }, status=403)
        
        if manpower.verification_status == 'REJECTED':
            return JsonResponse({
                "success": False,
                "message": "Your professional account has been rejected. Please contact support."
            }, status=403)
        
        manpower.is_available = not manpower.is_available
        manpower.save()
        return JsonResponse({"success": True, "is_available": manpower.is_available})
    return JsonResponse({"success": False}, status=400)


@login_required
def request_reverification(request):
    """Allow rejected professionals to request re-verification after fixing issues."""
    if request.method == 'POST':
        try:
            manpower_profile = get_object_or_404(ManpowerProfile, user=request.user)
            
            # Only allow re-verification request for rejected profiles
            if manpower_profile.verification_status != 'REJECTED':
                messages.error(request, "Your profile is not eligible for re-verification at this time.")
                return redirect('users:profile')
            
            # Change status back to PENDING
            manpower_profile.verification_status = 'PENDING'
            manpower_profile.rejection_reason = None  # Clear rejection reason
            manpower_profile.verified_at = None
            manpower_profile.verified_by = None
            manpower_profile.save(update_fields=['verification_status', 'rejection_reason', 'verified_at', 'verified_by'])
            
            messages.success(request, "Re-verification request submitted! Our admin team will review your profile shortly. You'll be notified once it's approved.")
            return redirect('users:profile')
            
        except ManpowerProfile.DoesNotExist:
            messages.error(request, "Professional profile not found.")
            return redirect('users:profile')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('users:profile')
    
    return redirect('users:profile')

User = get_user_model()
def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                phone = form.cleaned_data['phone_number'].strip()
                # Normalize phone number
                phone = re.sub(r'\s+', '', phone)
                user.phone_number = phone
                user.is_client = True
                user.is_professional = False
                user.save()
                
                # Store geolocation in session for later use in professional signup
                latitude = request.POST.get('location_latitude')
                longitude = request.POST.get('location_longitude')
                if latitude:
                    request.session['location_latitude'] = latitude
                if longitude:
                    request.session['location_longitude'] = longitude
                
                messages.success(request, "Account created successfully. Please log in.")
                return redirect('users:login')
            except Exception as e:
                messages.error(request, f"Signup error: {str(e)}")
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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
            
            # Try to get geolocation from POST data or session
            latitude = request.POST.get('latitude') or request.session.get('location_latitude')
            longitude = request.POST.get('longitude') or request.session.get('location_longitude')
            
            if latitude:
                try:
                    manpower_profile.latitude = float(latitude)
                except (ValueError, TypeError):
                    pass
            if longitude:
                try:
                    manpower_profile.longitude = float(longitude)
                except (ValueError, TypeError):
                    pass
            
            manpower_profile.save()
            form.save_m2m()
            
            # Clear location from session after use
            request.session.pop('location_latitude', None)
            request.session.pop('location_longitude', None)
            
            messages.success(request, "Profile created successfully.")
            return redirect('users:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ManpowerSignupForm(user=request.user)
        
        # Pre-populate latitude/longitude from session if available
        initial_data = {}
        if 'location_latitude' in request.session:
            initial_data['latitude'] = request.session['location_latitude']
        if 'location_longitude' in request.session:
            initial_data['longitude'] = request.session['location_longitude']
        if initial_data:
            form = ManpowerSignupForm(initial=initial_data, user=request.user)
    
    return render(request, 'users/professional_signup.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            auth_login(request, form.user)
            
            # Redirect admin users to admin panel
            if form.user.is_staff or form.user.is_superuser:
                return redirect('adminpanel:dashboard')
            
            next_page = request.POST.get('next') or request.GET.get('next')
            return redirect(next_page or 'home_module:home')
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


def get_provinces(request):
    """Return all provinces for dropdown population."""
    provinces = Province.objects.all().values('name')
    provinces_list = [{'name': p['name']} for p in provinces]
    return JsonResponse({'provinces': provinces_list})

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
    
    # Check verification status
    if pro.verification_status == 'PENDING':
        messages.error(request, "Your professional account is under review. You can access the dashboard only after approval.")
        return redirect('users:profile')
    
    if pro.verification_status == 'REJECTED':
        messages.error(request, "Your professional account has been rejected. Please contact support for more information.")
        return redirect('users:profile')
    
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
        from django.conf import settings
        api_key = settings.OPENROUTESERVICE_API_KEY
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