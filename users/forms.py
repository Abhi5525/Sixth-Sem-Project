import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Province, District, Municipality, CustomUser, ManpowerProfile
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class UserSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    phone_number = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))

    class Meta:
        model = User
        fields = ('full_name', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'usable_password' in self.fields:
            self.fields.pop('usable_password')
        self.fields['password1'].widget.attrs.update({'class': 'form-control','id': 'password1', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control','id': 'password2', 'placeholder': 'Confirm Password'})

    def clean_password1(self):
        password = self.cleaned_data.get('password1')

        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise forms.ValidationError(
                "Password must contain at least one letter and one number."
            )

        return password



    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Enter a valid phone number (10 digits).")
        return phone

class ManpowerSignupForm(forms.ModelForm):
    class Meta:
        model = ManpowerProfile
        fields = [ 'email', 'skill', 'province', 'district', 'municipality', 'ward', 'experience', 'citizenship_front', 'citizenship_back', 'rate', 'about_yourself']
        widgets = {
            'email':forms.EmailInput(attrs={'class':'form-control' ,'id':'email', 'placeholder':'Enter your email'}),
            'province': forms.Select(attrs={'class': 'form-control', 'id': 'province', 'placeholder': "e.g: Bagmati"}),
            'district': forms.Select(attrs={'class': 'form-control', 'id': 'district', 'placeholder': 'e.g: Kavrepalanchowk'}),
            'municipality': forms.Select(attrs={'class': 'form-control', 'id': 'municipality', 'placeholder': 'e.g: Budhanilkantha'}),
            'ward': forms.Select(attrs={'class': 'form-control', 'id': 'ward', 'placeholder': 'e.g: 1'}),
            'skill': forms.TextInput(attrs={'class': 'form-control','id':'skill', 'placeholder': 'Enter your Skills'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'years of experience'}),
            'citizenship_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citizenship_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'rate':forms.NumberInput(attrs={'class':'form-control',  'id':'rate', 'placeholder': 'Enter your rate per hour'}),
            'about_yourself': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about your experience and skills'}),
        }
        labels = {
            'rate': 'Rate/Hour',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the logged-in user from kwargs
        super().__init__(*args, **kwargs)
        if user:
            # Pre-fill fields from UserProfile or User
            # self.fields['full_name'].initial = user.full_name
            # self.fields['skill'].initial = user.manpowerprofile.skill
            # self.fields['province'].initial = user.manpowerprofile.province
            # self.fields['district'].initial = user.manpowerprofile.district
            # self.fields['municipality'].initial = user.manpowerprofile.municipality
            # self.fields['ward'].initial = user.manpowerprofile.ward
            # self.fields['experience'].initial = user.manpowerprofile.experience
            # self.fields['citizenship_front'].initial = user.manpowerprofile.citizenship_front
            # self.fields['citizenship_back'].initial = user.manpowerprofile.citizenship_back
            # self.fields['rate'].initial = user.manpowerprofile.rate

        # Populate province dropdown (optional, as JavaScript handles this)
            self.fields['province'].widget.choices = [('', '--- Select Province ---')] + [(p.name, p.name) for p in Province.objects.all()]

    def clean_province(self):
        province = self.cleaned_data.get('province')
        if province and not Province.objects.filter(name=province).exists():
            raise forms.ValidationError("Select a valid province.")
        return province

    def clean_district(self):
        district = self.cleaned_data.get('district')
        if district and not District.objects.filter(name=district).exists():
            raise forms.ValidationError("Select a valid district.")
        return district

    def clean_municipality(self):
        municipality = self.cleaned_data.get('municipality')
        if municipality and not Municipality.objects.filter(name=municipality).exists():
            raise forms.ValidationError("Select a valid municipality.")
        return municipality

    def clean_ward(self):
        ward = self.cleaned_data.get('ward')
        municipality = self.cleaned_data.get('municipality')
        if ward and municipality:
            try:
                municipality_obj = Municipality.objects.get(name=municipality)
                if int(ward) not in range(1, municipality_obj.ward + 1):
                    raise forms.ValidationError(f"Ward number must be between 1 and {municipality_obj.ward}.")
            except Municipality.DoesNotExist:
                raise forms.ValidationError("Invalid municipality selected.")
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid ward number format.")
        return ward
    
    def clean_experience(self):
        experience = self.cleaned_data.get('experience')
        if experience is not None and experience < 0:
            raise forms.ValidationError("Experience cannot be negative.")
        if experience is not None and experience > 50:
            raise forms.ValidationError("Experience seems unrealistic. Please enter a valid number.")
        return experience
    
    def clean_rate(self):
        rate = self.cleaned_data.get('rate')
        if rate is not None and rate <= 0:
            raise forms.ValidationError("Rate must be greater than 0.")
        if rate is not None and rate > 10000:
            raise forms.ValidationError("Rate seems too high. Please enter a realistic hourly rate.")
        return rate
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class LoginForm(forms.Form):
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'password',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        password = cleaned_data.get('password')
        
        if phone_number and password:
            # Validate phone number format
            user = authenticate(username=phone_number, password=password)
            if not user:
                raise forms.ValidationError("Invalid credentials")
            self.user = user
             
        return cleaned_data
    
class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone_number', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            if not phone.isdigit() or len(phone) != 10:
                raise forms.ValidationError("Enter a valid 10-digit phone number.")
            # Check if phone number is taken by another user
            if CustomUser.objects.exclude(pk=self.instance.pk).filter(phone_number=phone).exists():
                raise forms.ValidationError("This phone number is already registered.")
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is taken by another user
            if CustomUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise forms.ValidationError("This email is already registered.")
        return email


class ManpowerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = ManpowerProfile
        fields = [
            'skill', 'province', 'district', 'municipality', 'ward',
            'experience', 'citizenship_front', 'citizenship_back', 'rate',
            'profile_picture'
        ]
        widgets = {
            'skill': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'citizenship_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citizenship_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }    
    def clean_experience(self):
        experience = self.cleaned_data.get('experience')
        if experience is not None and experience < 0:
            raise forms.ValidationError("Experience cannot be negative.")
        if experience is not None and experience > 50:
            raise forms.ValidationError("Experience seems unrealistic. Please enter a valid number.")
        return experience
    
    def clean_rate(self):
        rate = self.cleaned_data.get('rate')
        if rate is not None and rate <= 0:
            raise forms.ValidationError("Rate must be greater than 0.")
        if rate is not None and rate > 10000:
            raise forms.ValidationError("Rate seems too high. Please enter a realistic hourly rate.")
        return rate
    
    def clean_ward(self):
        ward = self.cleaned_data.get('ward')
        if ward is not None and (ward < 1 or ward > 50):
            raise forms.ValidationError("Ward number must be between 1 and 50.")
        return ward