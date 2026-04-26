
import json
from django.shortcuts import get_object_or_404, render
from bookings.models import Booking,RatingReview
from users.models import ManpowerProfile
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ManpowerSerializer
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse   
from django.contrib import messages
from django.db.models import Q
from django.db.models import Avg, Count
from geopy.distance import great_circle
from django.views.decorators.csrf import ensure_csrf_cookie

PROFESSION_ALIASES = {
    'carpenter': ['carpentry'],
    'carpentry': ['carpenter'],
    'plumber': ['plumbing'],
    'plumbing': ['plumber'],
    'electrician': ['electrical'],
    'electrical': ['electrician'],
    'painter': ['painting'],
    'painting': ['painter'],
    'cleaner': ['cleaning'],
    'cleaning': ['cleaner'],
    'mason': ['masonry'],
    'masonry': ['mason'],
}


def build_search_terms(query):
    normalized = (query or '').strip().lower()
    if not normalized:
        return []

    terms = {normalized}
    terms.update(PROFESSION_ALIASES.get(normalized, []))
    return list(terms)


def save_user_location(request):
    if request.method != "POST":
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid coordinates'}, status=400)

    request.session['userLat'] = latitude
    request.session['userLng'] = longitude
    return JsonResponse({
        'success': True,
        'lat': request.session['userLat'],
        'lng': request.session['userLng']
    })
    
    
@ensure_csrf_cookie
def home(request):
    query = request.GET.get('searchInput')
    search_terms = build_search_terms(query)

    # First, check if user location exists in session
    user_lat = request.session.get("userLat")
    user_lon = request.session.get("userLng")

    # For professionals, fall back to their saved profile location when session location is missing.
    if (user_lat is None or user_lon is None) and request.user.is_authenticated and getattr(request.user, 'is_professional', False):
        try:
            pro_profile = ManpowerProfile.objects.get(user=request.user)
            if pro_profile.latitude is not None and pro_profile.longitude is not None:
                user_lat = pro_profile.latitude
                user_lon = pro_profile.longitude
        except ManpowerProfile.DoesNotExist:
            pass
    
    # Get today's bookings for logged-in users
    todays_bookings = []
    professional_status = None
    if request.user.is_authenticated:
        today = timezone.now().date()
        if request.user.is_professional:
            # Get professional's bookings for today
            try:
                pro_profile = ManpowerProfile.objects.get(user=request.user)
                todays_bookings = Booking.objects.filter(
                    professional=pro_profile,
                    booking_time__date=today,
                    is_confirmed=True,
                    status__in=['upcoming', 'ongoing']
                ).order_by('booking_time')
                # Pass verification status to template
                professional_status = {
                    'status': pro_profile.verification_status,
                    'rejection_reason': pro_profile.rejection_reason
                }
            except ManpowerProfile.DoesNotExist:
                pass
        elif request.user.is_client:
            # Get client's bookings for today
            todays_bookings = Booking.objects.filter(
                client=request.user,
                booking_time__date=today,
                is_confirmed=True,
                status__in=['upcoming', 'ongoing']
            ).order_by('booking_time')
    
    # Only show APPROVED professionals
    manpower_qs = ManpowerProfile.objects.select_related('user').filter(is_available=True, verification_status='APPROVED').annotate(
        live_average_rating=Avg('reviews_received__rating'),
        live_total_reviews=Count('reviews_received', distinct=True),
    )
    if search_terms:
        search_q = Q(skill__icontains=query)
        for term in search_terms:
            search_q |= Q(skills__name__icontains=term) | Q(skills__category__icontains=term)
        manpower_qs = manpower_qs.filter(search_q).distinct()

    manpower_list = None
    user_has_location = False

    # If we have a user location, compute distances and sort
    if user_lat is not None and user_lon is not None:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
            manpower_within_distance = []
            for manpower in manpower_qs:
                if manpower.latitude is not None and manpower.longitude is not None:
                    distance = great_circle((user_lat, user_lon), (float(manpower.latitude), float(manpower.longitude))).km
                    manpower.distance = distance
                else:
                    manpower.distance = None
                manpower_within_distance.append(manpower)

            manpower_within_distance.sort(key=lambda x: (x.distance is None, x.distance or 0.0))
            manpower_list = manpower_within_distance
            user_has_location = True
            nearest_with_distance = next((m for m in manpower_within_distance if m.distance is not None), None)
            if nearest_with_distance and nearest_with_distance.distance > 10:
                messages.info(request, "Here's the closest professionals to your location beyond 10 km.")
            if not manpower_within_distance:
                messages.info(request, "No professionals found matching your search criteria.")
        except (ValueError, TypeError):
            pass  # Location data conversion failed, fallback to unsorted list

    # Fallback: no location or error
    if manpower_list is None:
        manpower_list = manpower_qs
        if query and not manpower_qs.exists():
            messages.info(request, "No professionals found matching your search criteria.")

    # Paginate the manpower_list (works for lists and querysets)
    per_page = 9
    paginator = Paginator(manpower_list, per_page)
    page = request.GET.get('page')
    try:
        manpower_page = paginator.page(page)
    except PageNotAnInteger:
        manpower_page = paginator.page(1)
    except EmptyPage:
        manpower_page = paginator.page(paginator.num_pages)

    return render(request, 'home/index.html', {
        'manpower_list': manpower_page,
        'is_professional': request.user.is_authenticated and getattr(request.user, "is_professional", False),
        'user_has_location': user_has_location,
        'user_lat': user_lat,
        'user_lon': user_lon,
        'page_obj': manpower_page,
        'is_paginated': manpower_page.has_other_pages(),
        'todays_bookings': todays_bookings,
        'professional_status': professional_status,
    })


@login_required
def update_professional_location(request):
    if request.method == "POST" and request.user.is_professional:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON payload"}, status=400)

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return JsonResponse({"success": False, "error": "Invalid coordinates"}, status=400)

        profile = get_object_or_404(ManpowerProfile, user=request.user)
        profile.latitude = latitude
        profile.longitude = longitude
        profile.save()

        # Keep session location in sync so distance calculations work immediately.
        request.session['userLat'] = latitude
        request.session['userLng'] = longitude

        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@api_view(['GET'])
def manpower_list_api(request):
    queryset = ManpowerProfile.objects.select_related('user').filter(verification_status='APPROVED')
    serializer = ManpowerSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def manpower_detail_api(request, pk):
    try:
        manpower = ManpowerProfile.objects.select_related('user').get(pk=pk)
    except ManpowerProfile.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = ManpowerSerializer(manpower)
    return Response(serializer.data)


def professional_availability(request):
    now_utc = timezone.now()
    user_tz = timezone.get_current_timezone()
    
    # Find professionals who are currently busy
    active_bookings = Booking.objects.filter(
        booking_time__lte=now_utc,
        end_time__gte=now_utc,
        is_confirmed=True
    ).select_related('professional')
    
    booking_dict = {b.professional_id: b for b in active_bookings}
    
    professionals = ManpowerProfile.objects.select_related('user').filter(verification_status='APPROVED')
    data = []
    
    for prof in professionals:
        active_booking = booking_dict.get(prof.id)
        
        if active_booking:
            # Convert end time to user's local timezone for display
            local_end_time = timezone.localtime(active_booking.end_time, user_tz)
            
            # Calculate remaining time
            remaining_seconds = (active_booking.end_time - now_utc).total_seconds()
            
            if remaining_seconds > 0:
                hours, remainder = divmod(int(remaining_seconds), 3600)
                minutes = remainder // 60
                
                # Format different messages
                if hours >= 1:
                    message = f"Busy, free at {local_end_time.strftime('%I:%M %p')}"
                elif minutes > 1:
                    message = f"Busy, free in {minutes} minutes"
                else:
                    message = "Busy, finishing up"
                
                is_available = False
                status = "Busy"
            else:
                message = "Available"
                is_available = True
                status = "Available"
        else:
            message = "Available"
            is_available = True
            status = "Available"
        
        data.append({
            "id": prof.id,
            "status": status,
            "message": message,
            "is_available": is_available,
            "local_end_time": local_end_time.strftime("%I:%M %p") if active_booking else None,
        })
    
    return JsonResponse(data, safe=False)


@login_required
def review_page(request, professional_id):
    professional = get_object_or_404(ManpowerProfile, id=professional_id)
    return render(request, 'home/rating-review.html', {'professional': professional})

@login_required
def submit_review(request, professional_id):
    if request.method == "POST":
        try:
            rating = int(request.POST.get('rating'))
            comment = request.POST.get('comment', '').strip()
            
            # Validate rating range
            if not (1 <= rating <= 5):
                return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
            
            # Validate comment length
            if len(comment) > 500:
                return JsonResponse({'error': 'Comment cannot exceed 500 characters'}, status=400)
                
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid rating value'}, status=400)

        professional = get_object_or_404(ManpowerProfile, id=professional_id)

        # Ensure the user has booked this professional before reviewing
        booking = Booking.objects.filter(
            professional=professional,
            client=request.user,
            is_confirmed=True
        ).order_by('-booking_time').first()

        if not booking:
            return JsonResponse({'error': 'You can only review professionals you have booked.'}, status=403)

        # Create or update review for that booking
        RatingReview.objects.update_or_create(
            booking=booking,
            reviewer=request.user,
            professional=professional,
            defaults={'rating': rating, 'comment': comment}
        )

        return JsonResponse({'success': True, 'message': 'Review submitted successfully!'})

    return JsonResponse({'error': 'Invalid request'}, status=400)