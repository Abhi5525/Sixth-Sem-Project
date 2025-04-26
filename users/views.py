

# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.urls import reverse
from .forms import UserSignupForm, ManpowerSignupForm
from .models import UserProfile, ManpowerProfile

def profile(request):
    return render(request, 'users/profile.html')

def signup_choice(request):
    return render(request, 'users/signup_choice.html')

def user_signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name'],
                phone_number=form.cleaned_data['phone_number']
            )
            return redirect('users:login')
    else:
        form = UserSignupForm()
    return render(request, 'users/user_signup.html', {'form': form})

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

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    def get_success_url(self):
        return reverse('users:profile')