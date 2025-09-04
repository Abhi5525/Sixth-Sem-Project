
# users/views.py
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

@login_required             
def profile(request):
    user = request.user
    manpower_profile = None
    if user.is_professional:
        manpower_profile = get_object_or_404(ManpowerProfile, user=user)

    user_form = UserProfileUpdateForm(instance=user)
    profile_form = ManpowerProfileUpdateForm(instance=manpower_profile) if manpower_profile else None

    return render(request, "users/profile.html", {
        "user": user,
        "manpower_profile": manpower_profile,
        "user_form": user_form,
        "profile_form": profile_form,
    })


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
            # user.username = form.cleaned_data['email'].split('@')[0]+ str(User.objects.count())
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
  