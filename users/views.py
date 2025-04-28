
# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView
from django.urls import reverse
from .forms import UserSignupForm, LoginForm, ManpowerSignupForm
from .models import UserProfile, ManpowerProfile
from home import views

def profile(request):
    return render(request, 'users/profile.html')

# def signup_choice(request):
#     return render(request, 'users/signup_choice.html')

def signup(request):
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