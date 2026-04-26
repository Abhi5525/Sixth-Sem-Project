import json
import uuid
import base64
import hmac
import hashlib
import logging
import re
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Booking, Payment
from django.utils import timezone

from django.conf import settings
from django.http import JsonResponse
from users.models import ManpowerProfile 
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime, parse_date
from decimal import Decimal
from datetime import timedelta, datetime, timezone as dt_timezone

logger = logging.getLogger(__name__)

BOOKING_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s\-']{2,99}$")
BOOKING_PHONE_PATTERN = re.compile(r"^98\d{8}$")
BOOKING_START_HOUR = 6
BOOKING_END_HOUR = 20
BOOKING_SLOT_INTERVAL_MINUTES = 30


def _round_up_to_slot(dt_obj, interval_minutes=BOOKING_SLOT_INTERVAL_MINUTES):
    dt_obj = dt_obj.replace(second=0, microsecond=0)
    remainder = dt_obj.minute % interval_minutes
    if remainder == 0:
        return dt_obj
    return dt_obj + timedelta(minutes=(interval_minutes - remainder))


def _calculate_available_slots(professional, selected_date, duration_hours):
    current_tz = timezone.get_current_timezone()
    selected_day_start_local = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()), current_tz)
    selected_day_end_local = selected_day_start_local + timedelta(days=1)

    open_start_local = selected_day_start_local.replace(hour=BOOKING_START_HOUR, minute=0, second=0, microsecond=0)
    open_end_local = selected_day_start_local.replace(hour=BOOKING_END_HOUR, minute=0, second=0, microsecond=0)

    latest_start_local = open_end_local - timedelta(hours=duration_hours)
    if latest_start_local < open_start_local:
        return []

    min_start_local = open_start_local
    now_local = timezone.localtime(timezone.now())
    if selected_date == now_local.date():
        min_start_local = max(min_start_local, now_local + timedelta(minutes=30))
    min_start_local = _round_up_to_slot(min_start_local)

    if min_start_local > latest_start_local:
        return []

    selected_day_start_utc = selected_day_start_local.astimezone(dt_timezone.utc)
    selected_day_end_utc = selected_day_end_local.astimezone(dt_timezone.utc)

    busy_bookings = Booking.objects.filter(
        professional=professional,
        booking_time__lt=selected_day_end_utc,
        end_time__gt=selected_day_start_utc,
    )

    busy_ranges = []
    for booking in busy_bookings:
        booking_start_local = timezone.localtime(booking.booking_time, current_tz)
        booking_end_local = timezone.localtime(booking.end_time, current_tz)
        # Keep one slot-gap after each booking before next booking can start.
        booking_end_with_gap = booking_end_local + timedelta(minutes=BOOKING_SLOT_INTERVAL_MINUTES)
        busy_ranges.append((booking_start_local, booking_end_with_gap))

    available_slots = []
    cursor = min_start_local
    while cursor <= latest_start_local:
        slot_end = cursor + timedelta(hours=duration_hours)
        is_overlapping = any(cursor < busy_end and slot_end > busy_start for busy_start, busy_end in busy_ranges)
        if not is_overlapping:
            available_slots.append({
                'value': cursor.strftime('%H:%M'),
                'label': cursor.strftime('%I:%M %p')
            })
        cursor += timedelta(minutes=BOOKING_SLOT_INTERVAL_MINUTES)

    return available_slots


@login_required
def available_slots(request, professional_id):
    professional = get_object_or_404(
        ManpowerProfile,
        id=professional_id,
        verification_status='APPROVED',
        user__is_professional=True
    )

    selected_date_str = request.GET.get('date')
    duration_raw = request.GET.get('duration_hours') or '1'

    selected_date = parse_date(selected_date_str or '')
    if not selected_date:
        return JsonResponse({'success': False, 'error': 'Invalid date'}, status=400)

    try:
        duration_hours = float(duration_raw)
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid duration'}, status=400)

    if duration_hours < 0.5 or duration_hours > 24:
        return JsonResponse({'success': False, 'error': 'Duration must be between 0.5 and 24 hours'}, status=400)

    slots = _calculate_available_slots(professional, selected_date, duration_hours)
    return JsonResponse({'success': True, 'slots': slots})

@login_required
def booking_form(request, professional_id):
    # Ensure professional is APPROVED and available
    professional = get_object_or_404(
        ManpowerProfile,
        id=professional_id,
        verification_status='APPROVED',
        user__is_professional=True
    )
    
    prof_lat = professional.latitude or 27.7
    prof_lng = professional.longitude or 85.3

    # Keep booking page aware of last session location for fallback.
    session_user_lat = request.session.get('userLat')
    session_user_lng = request.session.get('userLng')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = (data.get('name') or '').strip()
            phone = (data.get('phone') or '').strip()

            if not BOOKING_NAME_PATTERN.fullmatch(name):
                return JsonResponse({
                    'success': False,
                    'error': 'Name must start with a letter and contain at least 3 valid characters.'
                }, status=400)

            if len(re.sub(r"[^A-Za-z]", "", name)) < 3:
                return JsonResponse({
                    'success': False,
                    'error': 'Name must contain at least 3 letters.'
                }, status=400)

            if not BOOKING_PHONE_PATTERN.fullmatch(phone):
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number must be 10 digits and start with 98.'
                }, status=400)
            
            # Parse booking time
            booking_time_str = data.get('booking_time')
            booking_time = parse_datetime(booking_time_str)
            if booking_time is None:
                return JsonResponse({'success': False, 'error': 'Invalid booking time format'}, status=400)
            
            # Make timezone-aware UTC
            if not timezone.is_aware(booking_time):
                booking_time = timezone.make_aware(booking_time, timezone=dt_timezone.utc)

            # Enforce booking window in local timezone: 6:00 AM to 7:59 PM.
            local_booking_time = timezone.localtime(booking_time)
            if local_booking_time.hour < BOOKING_START_HOUR or local_booking_time.hour >= BOOKING_END_HOUR:
                return JsonResponse({
                    'success': False,
                    'error': 'Bookings are allowed only between 6:00 AM and 8:00 PM.'
                }, status=400)
            
            # Parse duration
            duration_hours_raw = data.get('duration_hours') or 1
            duration_hours = float(duration_hours_raw)

            # Calculate end time
            end_time = booking_time + timedelta(hours=duration_hours)

            # ... rest of your code ...
            user_lat_raw = data.get('latitude')
            user_lng_raw = data.get('longitude')

            # Fallback to session coordinates when client storage is missing/stale.
            if user_lat_raw in (None, '') or user_lng_raw in (None, ''):
                user_lat_raw = request.session.get('userLat')
                user_lng_raw = request.session.get('userLng')

            if not user_lat_raw or not user_lng_raw:
                return JsonResponse({'success': False, 'error': 'Location missing'}, status=400)

            user_lat = float(user_lat_raw)
            user_lng = float(user_lng_raw)


            # Calculate fees using Decimal for precision
            rate = Decimal(str(professional.rate))  # Ensure professional.rate exists
            
            total_fee = (rate * Decimal(str(duration_hours))).quantize(Decimal('0.01'))
            deposit = (total_fee * Decimal('0.10')).quantize(Decimal('0.01'))

            # Create booking
            booking = Booking(
                client=request.user,
                client_name=name,
                client_phone=phone,
                professional=professional,
                booking_time=booking_time,
                duration_hours=duration_hours,
                end_time=end_time,  # Add this field to your model if not present
                total_fee=total_fee,
                deposit_amount=deposit,
                user_latitude=user_lat,
                user_longitude=user_lng,
                professional_latitude=prof_lat,
                professional_longitude=prof_lng
            )

            booking.full_clean()
            booking.save()

            # Create payment record for deposit
            Payment.objects.create(booking=booking, amount=deposit)

            return JsonResponse({'success': True, 'booking_id': booking.id})

        except (KeyError, ValueError, ValidationError) as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'bookings/booking_form.html', {
        'professional': professional,
        'prof_lat': prof_lat,
        'prof_lng': prof_lng,
        'user_lat': session_user_lat,
        'user_lng': session_user_lng,
        'default_client_name': request.user.full_name or '',
        'default_client_phone': request.user.phone_number or '',
    })




# ---------------------------
# Utility: generate eSewa signature
# ---------------------------
def generate_signature(payment_data, secret_key):
    signed_fields = payment_data['signed_field_names'].split(',')
    message = ','.join(f"{field}={payment_data[field]}" for field in signed_fields)
    signature = base64.b64encode(
        hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')
    return signature

# ---------------------------
# Checkout view
# ---------------------------
@login_required
def checkout(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, client=request.user)
    payment = get_object_or_404(Payment, booking=booking)

    # Amounts
    amount = f"{booking.deposit_amount:.2f}"
    tax_amount = "0"
    total_amount = f"{Decimal(amount) + Decimal(tax_amount):.2f}"

    # Prepare form data for eSewa RC sandbox
    form_data = {
        'amount': amount,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'transaction_uuid': str(payment.transaction_uuid),
        'product_code': 'EPAYTEST',
        'product_service_charge': '0',
        'product_delivery_charge': '0',
        'success_url': 'http://localhost:8000/bookings/esewa-callback/',
        'failure_url': 'http://localhost:8000/bookings/payment-failed/',
        'signed_field_names': 'total_amount,transaction_uuid,product_code',
    }
    form_data['signature'] = generate_signature(form_data, "8gBm/:&EnhH.1/q")

    context = {
        'booking': booking,
        'form_data': form_data,
        'esewa_url': 'https://rc-epay.esewa.com.np/api/epay/main/v2/form',
    }

    logger.info(f"Checkout initiated for booking {booking.id}. Form data: {form_data}")
    return render(request, 'bookings/checkout.html', context)

@csrf_exempt
def esewa_callback(request):
    logger.info(f"eSewa callback received. Method: {request.method}")
    logger.info(f"GET data: {request.GET}")
    logger.info(f"POST data: {request.POST}")

    data_param = request.GET.get('data') or request.POST.get('data')
    if not data_param:
        logger.error("eSewa callback: Missing 'data' parameter")
        return redirect('bookings:payment_failed')

    try:
        # Decode base64 -> JSON
        decoded_data = base64.b64decode(data_param).decode('utf-8')
        payment_data = json.loads(decoded_data)
        logger.info(f"Decoded eSewa data: {payment_data}")
    except Exception as e:
        logger.error(f"Failed to decode eSewa data: {str(e)}")
        return redirect('bookings:payment_failed')

    # Extract fields
    transaction_code = payment_data.get('transaction_code')
    status = payment_data.get('status')
    total_amount = payment_data.get('total_amount')
    transaction_uuid = payment_data.get('transaction_uuid')
    product_code = payment_data.get('product_code')

    missing = [k for k,v in zip(
        ['transaction_code','status','total_amount','transaction_uuid','product_code'],
        [transaction_code,status,total_amount,transaction_uuid,product_code]
    ) if not v]
    if missing:
        logger.error(f"Missing fields after decoding: {missing}")
        return redirect('bookings:payment_failed')

    # Retrieve payment & booking
    payment = get_object_or_404(Payment, transaction_uuid=transaction_uuid)
    booking = payment.booking

    # Check status
    if status != 'COMPLETE':
        logger.error(f"Payment not complete. Status: {status}")
        return redirect('bookings:payment_failed')

    # Check amount
    if Decimal(total_amount) != booking.deposit_amount:
        logger.error(f"Amount mismatch: {total_amount} vs {booking.deposit_amount}")
        return redirect('bookings:payment_failed')

    # Mark payment successful
    payment.is_paid = True
    payment.payment_date = timezone.now()
    payment.esewa_ref_id = transaction_code
    payment.esewa_order_id = transaction_uuid
    payment.save()

    booking.is_confirmed = True
    booking.save()
    logger.info(f"Payment successful for booking {booking.id}, transaction {transaction_uuid}")

    return render(request, 'bookings/payment_success.html', {'booking': booking})

@login_required
def payment_failed(request):
    return render(request, 'bookings/payment_failed.html')

@login_required
def bookings(request):
    user = request.user
    now_utc = timezone.now()  # This is in UTC when USE_TZ=True

    # Upcoming bookings - filter in UTC and ensure they belong to current user
    upcoming_bookings = Booking.objects.filter(
        client=user,
        booking_time__gte=now_utc
    ).select_related('professional__user').order_by('booking_time')

    # Past bookings - filter in UTC and ensure they belong to current user
    past_bookings = Booking.objects.filter(
        client=user,
        booking_time__lt=now_utc
    ).select_related('professional__user').order_by('-booking_time')
    
    # Process bookings - NO local time conversion here
    for booking in list(upcoming_bookings) + list(past_bookings):
        # Determine status based on UTC comparison
        if booking.booking_time < now_utc:  # Compare UTC with UTC
            booking.status = 'completed'
        else:
            booking.status = 'upcoming'
        
        # Attach payment information
        try:
            booking.payment
        except Payment.DoesNotExist:
            booking.payment = None

        # Remaining balance calculation
        booking.remaining_balance = booking.total_fee - booking.deposit_amount

    return render(request, 'bookings/bookings.html', {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
    })



def payment_Success(request):
    return render(request, 'bookings/payment_success.html')
