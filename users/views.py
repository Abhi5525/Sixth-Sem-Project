
# users/views.py
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login ,get_user_model
from django.urls import reverse
from .forms import ManpowerProfileUpdateForm, UserProfileUpdateForm, UserSignupForm, LoginForm, ManpowerSignupForm
from users.models import UserProfile, ManpowerProfile
from home import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django import forms


@login_required
def profile(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user) 
    return render(request, 'users/profile.html', {'user_profile': user_profile})
    

# def signup_choice(request):
#     return render(request, 'users/signup_choice.html')
User = get_user_model()
def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit= False)
            user.username = form.cleaned_data['email'].split('@')[0]+ str(User.objects.count())
            user.save()
            UserProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                phone_number=form.cleaned_data['phone_number']
            )
            return redirect('users:login')
    else:
        form = UserSignupForm()
    return render(request, 'users/signup.html', {'form': form})

def professional_signup(request):
    if request.method == 'POST':
        form = ManpowerSignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            ManpowerProfile.objects.create(
                user=user,
                name=form.cleaned_data['name'],
                address=form.cleaned_data['address'],
                phone=form.cleaned_data['phone'],
                skill=form.cleaned_data['skill'],
                experience_years=form.cleaned_data['experience_years'],
                photo=form.cleaned_data['photo'],
                citizenship_front=form.cleaned_data['citizenship_front'],
                citizenship_back=form.cleaned_data['citizenship_back']
            )
            return redirect('users:login')
    else:
        form = ManpowerSignupForm()
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
            profile = UserProfile.objects.get(user=user)
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
        
    except (UserProfile.DoesNotExist, ManpowerProfile.DoesNotExist):
        raise Http404("Profile not found")
    
class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)
    template_name='users/login.html'