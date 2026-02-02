from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum
from users.models import ManpowerProfile, CustomUser
from bookings.models import Booking, Payment
from django.core.paginator import Paginator

def is_admin(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def admin_login_required(view_func):
    """Custom decorator combining login_required and admin check"""
    @login_required(login_url='users:login')
    @user_passes_test(is_admin, login_url='users:login')
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, 'You must be an administrator to access this page.')
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_login_required
def admin_dashboard(request):
    """Main admin dashboard with statistics"""
    # Get statistics
    total_professionals = ManpowerProfile.objects.count()
    pending_verifications = ManpowerProfile.objects.filter(verification_status='PENDING').count()
    approved_professionals = ManpowerProfile.objects.filter(verification_status='APPROVED').count()
    rejected_professionals = ManpowerProfile.objects.filter(verification_status='REJECTED').count()
    
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(is_confirmed=True).count()
    completed_bookings = Booking.objects.filter(status='completed').count()
    
    total_clients = CustomUser.objects.filter(is_client=True).count()
    total_revenue = Payment.objects.filter(is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Recent pending verifications
    recent_pending = ManpowerProfile.objects.filter(
        verification_status='PENDING'
    ).select_related('user').order_by('-id')[:5]
    
    # Recent bookings
    recent_bookings = Booking.objects.select_related('client', 'professional__user').order_by('-booking_time')[:5]
    
    context = {
        'total_professionals': total_professionals,
        'pending_verifications': pending_verifications,
        'approved_professionals': approved_professionals,
        'rejected_professionals': rejected_professionals,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'completed_bookings': completed_bookings,
        'total_clients': total_clients,
        'total_revenue': total_revenue,
        'recent_pending': recent_pending,
        'recent_bookings': recent_bookings,
    }
    
    return render(request, 'adminpanel/dashboard.html', context)

@admin_login_required
def pending_verifications(request):
    """List all pending professional verifications"""
    pending_list = ManpowerProfile.objects.filter(
        verification_status='PENDING'
    ).select_related('user').order_by('-id')
    
    # Pagination
    paginator = Paginator(pending_list, 10)
    page = request.GET.get('page')
    pending_professionals = paginator.get_page(page)
    
    context = {
        'pending_professionals': pending_professionals,
        'page_obj': pending_professionals,
    }
    
    return render(request, 'adminpanel/pending_verifications.html', context)

@admin_login_required
def all_professionals(request):
    """List all professionals with filter options"""
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    professionals_list = ManpowerProfile.objects.select_related('user').all()
    
    # Apply filters
    if status_filter != 'all':
        professionals_list = professionals_list.filter(verification_status=status_filter.upper())
    
    if search_query:
        professionals_list = professionals_list.filter(
            Q(user__full_name__icontains=search_query) |
            Q(skill__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    professionals_list = professionals_list.order_by('-id')
    
    # Pagination
    paginator = Paginator(professionals_list, 15)
    page = request.GET.get('page')
    professionals = paginator.get_page(page)
    
    context = {
        'professionals': professionals,
        'page_obj': professionals,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'adminpanel/all_professionals.html', context)

@admin_login_required
def professional_detail(request, pk):
    """View detailed information about a professional"""
    professional = get_object_or_404(ManpowerProfile.objects.select_related('user'), pk=pk)
    
    # Check if rate is valid
    rate_valid = True
    rate_error = None
    try:
        professional.check_rate()
    except ValueError as e:
        rate_valid = False
        rate_error = str(e)
    
    # Get professional's bookings
    bookings = Booking.objects.filter(professional=professional).select_related('client').order_by('-booking_time')[:10]
    
    context = {
        'professional': professional,
        'bookings': bookings,
        'rate_valid': rate_valid,
        'rate_error': rate_error,
    }
    
    return render(request, 'adminpanel/professional_detail.html', context)

@admin_login_required
def approve_professional(request, pk):
    """Approve a professional's verification"""
    if request.method == 'POST':
        professional = get_object_or_404(ManpowerProfile, pk=pk)
        
        # Validate rate before approval
        try:
            professional.check_rate()
        except ValueError as e:
            error_msg = f'Cannot approve {professional.user.full_name}: {str(e)}'
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg})
            
            return redirect('adminpanel:pending_verifications')
        
        # If validation passes, approve the professional
        professional.verification_status = 'APPROVED'
        professional.verified_at = timezone.now()
        professional.verified_by = request.user
        professional.rejection_reason = None
        professional.save(update_fields=['verification_status', 'verified_at', 'verified_by', 'rejection_reason'])
        
        messages.success(request, f'{professional.user.full_name} has been approved successfully!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Professional approved successfully'})
        
        return redirect('adminpanel:pending_verifications')
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@admin_login_required
def reject_professional(request, pk):
    """Reject a professional's verification"""
    if request.method == 'POST':
        professional = get_object_or_404(ManpowerProfile, pk=pk)
        rejection_reason = request.POST.get('rejection_reason', 'Not specified')
        
        professional.verification_status = 'REJECTED'
        professional.verified_at = timezone.now()
        professional.verified_by = request.user
        professional.rejection_reason = rejection_reason
        professional.save(update_fields=['verification_status', 'verified_at', 'verified_by', 'rejection_reason'])
        
        messages.warning(request, f'{professional.user.full_name} has been rejected.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Professional rejected'})
        
        return redirect('adminpanel:pending_verifications')
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@admin_login_required
def toggle_availability(request, pk):
    """Toggle professional availability status"""
    if request.method == 'POST':
        professional = get_object_or_404(ManpowerProfile, pk=pk)
        professional.is_available = not professional.is_available
        professional.save(update_fields=['is_available'])
        
        status = 'available' if professional.is_available else 'unavailable'
        messages.info(request, f'{professional.user.full_name} is now {status}.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'is_available': professional.is_available})
        
        return redirect(request.META.get('HTTP_REFERER', 'adminpanel:all_professionals'))
    
    return JsonResponse({'success': False}, status=400)

@admin_login_required
def all_bookings(request):
    """View all bookings in the system"""
    status_filter = request.GET.get('status', 'all')
    
    bookings_list = Booking.objects.select_related('client', 'professional__user').all()
    
    if status_filter != 'all':
        bookings_list = bookings_list.filter(status=status_filter.lower())
    
    bookings_list = bookings_list.order_by('-booking_time')
    
    # Pagination
    paginator = Paginator(bookings_list, 20)
    page = request.GET.get('page')
    bookings = paginator.get_page(page)
    
    context = {
        'bookings': bookings,
        'page_obj': bookings,
        'status_filter': status_filter,
    }
    
    return render(request, 'adminpanel/all_bookings.html', context)

