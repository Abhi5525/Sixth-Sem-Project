
# users/views.py
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login ,get_user_model
from django.urls import reverse
from .forms import ManpowerProfileUpdateForm, UserProfileUpdateForm, UserSignupForm, LoginForm, ManpowerSignupForm
from users.models import CustomUser, ManpowerProfile, District, Municipality, Province
from home import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django import forms

@login_required
def profile(request):
    user = request.user  # CustomUser
    try:
        manpower_profile = ManpowerProfile.objects.get(user=user)
    except ManpowerProfile.DoesNotExist:
        manpower_profile = None
    return render(request, 'users/profile.html', {
        'user': user,
        'manpower_profile': manpower_profile
    })


# def signup_choice(request):
#     return render(request, 'users/signup_choice.html')
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
            manpower_profile.save()
            messages.success(request, "Profile created successfully.")
            return redirect('users:profile')  # Adjust to your profile URL
        else:
            messages.error(request, "Please correct the errors below.")
            print(form.errors)
    else:
        form = ManpowerSignupForm(user=request.user)
    return render(request, 'users/professional_signup.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            auth_login(request, form.user)
            return redirect('home_module:home')
           
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form':form})

@login_required
def profile_update(request):
    user = request.user
    profile_type = request.GET.get('type', 'user')  # Default to user profile
    
    try:
        # Determine which profile to update
        if profile_type == 'manpower':
            profile = ManpowerProfile.objects.get(user=user)
            form_class = ManpowerProfileUpdateForm
            # success_url = reverse('users:manpower_profile')
        else:
            profile = user
            form_class = UserProfileUpdateForm
        
        success_url = reverse('users:profile')
        if request.method == 'POST':
            form = form_class(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': "Profile updated successfully."
                    })
                messages.success(request, "Profile updated successfully.")
                return redirect(success_url)
        else:
            form = form_class(instance=profile)
            
        # For AJAX requests, return just the form HTML
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'users/profile.html', {'form': form})
            
        return render(request, 'users/profile.html', {'form': form})
        
    except (ManpowerProfile.DoesNotExist, CustomUser.DoesNotExist):
        raise Http404("Profile not found")
    
class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)
    template_name='users/login.html'


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