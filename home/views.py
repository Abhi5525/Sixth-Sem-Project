
import json
from django.shortcuts import get_object_or_404, render
from bookings.models import Booking
from users.models import ManpowerProfile, CustomUser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ManpowerSerializer
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse   
from django.contrib import messages
# Create your views here.
from django.db.models import Q
from bookings.models import RatingReview

def home(request):
    query = request.GET.get('searchInput')
    
    if query:
        manpower_list = ManpowerProfile.objects.select_related('user').filter(
            Q(skill__icontains=query) | Q(user__full_name__icontains=query),
            is_available=True
        )
        if not manpower_list.exists():
            messages.info(request, "No professionals found matching your search criteria.")
    else:
        manpower_list = ManpowerProfile.objects.filter(is_available=True).select_related('user')
        
    return render(request, 'home/index.html', {
        'ManpowerList': manpower_list,
        'is_professional': request.user.is_authenticated and getattr(request.user, "is_professional", False)
 
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

# @login_required
# def find_professionals(request):
#     if request.method == 'POST':
#         latitude = float(request.POST.get('latitude'))
#         longitude = float(request.POST.get('longitude'))
#         skill = request.POST.get('skill')

#         user_location = Point(longitude, latitude, srid=4326)
#         professionals = CustomUser.objects.filter(
#             user_type='professional',
#             manpowerprofile__is_available=True,
#             manpowerprofile__skill=skill,
#             manpowerprofile__location__distance_lte=(user_location, D(km=10))
#         ).annotate(
#             distance=Distance('manpowerprofile__location', user_location)
#         ).order_by('distance')

#         return render(request, 'home/index.html', {'professionals': professionals})
#     return render(request, 'home/index.html')

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


def get_galli_maps_token(request):
    """Return the Galli Maps API key securely"""
    return JsonResponse({"token": settings.GALLIMAPS_API_KEY})



def professional_availability(request):
    now = timezone.now()

    active_bookings = Booking.objects.filter(
        booking_time__lte=now,
        end_time__gte=now,
        is_confirmed=True
    ).select_related('professional')

    booking_dict = {b.professional_id: b for b in active_bookings}

    professionals = ManpowerProfile.objects.select_related('user').all()
    data = []

    for prof in professionals:
        active_booking = booking_dict.get(prof.id)
        if active_booking:
            remaining = (active_booking.end_time - now).total_seconds()
            hours, remainder = divmod(int(remaining), 3600)
            minutes = remainder // 60
            status = "Busy"
            message = f"Free in {hours}h {minutes}m"
            is_available = False
            
        else:
            status = "Available"
            message = "Available"
            is_available = True
           

        data.append({
            "id": prof.id,
            "status": status,
            "message": message,
            "is_available": is_available,
            
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