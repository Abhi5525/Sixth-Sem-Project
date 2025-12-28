
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
from geopy.distance import great_circle


def save_user_location(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session['userLat'] = data.get("latitude")
        request.session['userLng'] = data.get("longitude")
        return JsonResponse({
            'success': True,
            'lat': request.session['userLat'],
            'lng': request.session['userLng']})
    
    
def home(request):
    query = request.GET.get('searchInput')

    # First, check if user location exists in session
    user_lat = request.session.get("userLat")
    user_lon = request.session.get("userLng")
    
    # Debug print to see what's in session
    print("User Location from session:", user_lat, user_lon)
    
    manpower_qs = ManpowerProfile.objects.select_related('user').filter(is_available=True)
    if query:
        manpower_qs = manpower_qs.filter(
            Q(skill__icontains=query) | Q(user__full_name__icontains=query)
        )

    manpower_list = None
    user_has_location = False

    # If we have a user location, compute distances and sort
    if user_lat and user_lon:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
            manpower_within_distance = []
            for manpower in manpower_qs:
                if manpower.latitude and manpower.longitude:
                    distance = great_circle((user_lat, user_lon), (float(manpower.latitude), float(manpower.longitude))).km
                    manpower.distance = distance
                else:
                    manpower.distance = float('inf')
                manpower_within_distance.append(manpower)

            manpower_within_distance.sort(key=lambda x: x.distance)
            manpower_list = manpower_within_distance
            user_has_location = True
            if manpower_within_distance and manpower_within_distance[0].distance > 10:
                messages.info(request, "Here's the closest professionals to your location beyond 10 km.")
            if not manpower_within_distance:
                messages.info(request, "No professionals found matching your search criteria.")
        except (ValueError, TypeError) as e:
            print(f"Error converting location data: {e}")

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
        'page_obj': manpower_page,
        'is_paginated': manpower_page.has_other_pages(),
    })


@login_required
def update_professional_location(request):
    if request.method == "POST" and request.user.is_professional:
        data = json.loads(request.body)
        profile = get_object_or_404(ManpowerProfile, user=request.user)
        profile.latitude = data.get("latitude")
        profile.longitude = data.get("longitude")
        profile.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@api_view(['GET'])
def manpower_list_api(request):
    queryset = ManpowerProfile.objects.select_related('user').all()
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


def maps(request):
    return render(request, 'home/index_POC.html')

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
    
    professionals = ManpowerProfile.objects.select_related('user').all()
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