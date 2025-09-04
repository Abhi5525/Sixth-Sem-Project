import json
from django.shortcuts import render
import logging
import hashlib
import hmac
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Booking, Payment
import requests
import xmltodict
from django.conf import settings
from django.http import JsonResponse
from users.models import ManpowerProfile 
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from decimal import Decimal
from datetime import timedelta
import traceback
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@login_required
def booking_form(request, professional_id):
    
    professional = get_object_or_404(ManpowerProfile, id=professional_id)

    # Defaults if professional location is not set
    prof_lat = professional.latitude or 27.7
    prof_lng = professional.longitude or 85.3

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            
            # Parse booking time
            booking_time_str = data.get('booking_time')
            booking_time = parse_datetime(booking_time_str)
            if booking_time is None:
                return JsonResponse({'success': False, 'error': 'Invalid booking time format'}, status=400)

            # Parse duration
            duration_hours = float(data.get('duration_hours', 1))
            if duration_hours <= 0:
                return JsonResponse({'success': False, 'error': 'Duration must be positive'}, status=400)

            # Calculate end time
            end_time = booking_time + timedelta(hours=duration_hours)

            # Parse user location
            user_lat = float(data.get('latitude'))
            user_lng = float(data.get('longitude'))

            # Calculate fees using Decimal for precision
            rate = Decimal(str(professional.rate))  # Ensure professional.rate exists
            total_fee = (rate * Decimal(str(duration_hours))).quantize(Decimal('0.01'))
            deposit = (total_fee * Decimal('0.10')).quantize(Decimal('0.01'))

            # Create booking
            booking = Booking.objects.create(
                client=request.user,
                client_name=name,
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

            # Create payment record for deposit
            Payment.objects.create(booking=booking, amount=deposit)

            return JsonResponse({'success': True, 'booking_id': booking.id})

        except (KeyError, ValueError, ValidationError) as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'bookings/booking_form.html', {
        'professional': professional,
        'prof_lat': prof_lat,
        'prof_lng': prof_lng
    })



def generate_signature(payment_data, secret_key):
    """
    Generates eSewa signature based on signed_field_names
    """
    signed_fields = payment_data['signed_field_names'].split(',')
    message = ','.join(f"{field}={payment_data[field]}" for field in signed_fields)
    signature = base64.b64encode(
        hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')
    return signature
import json
import uuid
import base64
import hmac
import hashlib
import logging
from decimal import Decimal
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Booking, Payment

logger = logging.getLogger(__name__)

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
    booking = get_object_or_404(Booking, id=booking_id)
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

def payment_failed(request):
    return render(request, 'bookings/payment_failed.html')
# Create your views here.
def bookings(request):
    user = request.user
    now = timezone.now()

    # Upcoming bookings
    upcoming_bookings = Booking.objects.filter(
        client=user,
        booking_time__gte=now
    ).select_related('professional__user').order_by('booking_time')

    # Past bookings
    past_bookings = Booking.objects.filter(
        client=user,
        booking_time__lt=now
    ).select_related('professional__user').order_by('-booking_time')

    # Attach payment and remaining balance
    for booking in list(upcoming_bookings) + list(past_bookings):
        try:
            booking.payment
        except Payment.DoesNotExist:
            booking.payment = None

        # Remaining balance calculation (total minus deposit)
        booking.remaining_balance = booking.total_fee - booking.deposit_amount

        if booking.booking_time < now:
            booking.status = 'completed'  # adjust if you have real status field

    return render(request, 'bookings/bookings.html', {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings
    })

def payment_Success(request):
    return render(request, 'bookings/payment_success.html')
