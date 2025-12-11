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
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})


    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Enter a valid phone number (10 digits).")
        return phone

class ManpowerSignupForm(forms.ModelForm):
    class Meta:
        model = ManpowerProfile
        fields = [ 'email', 'skill', 'province', 'district', 'municipality', 'ward', 'experience', 'citizenship_front', 'citizenship_back', 'rate']
        widgets = {
            'email':forms.EmailInput(attrs={'class':'form-control' ,'id':'email', 'placeholder':'Enter your email'}),
            'province': forms.Select(attrs={'class': 'form-control', 'id': 'province', 'placeholder': "e.g: Bagmati"}),
            'district': forms.Select(attrs={'class': 'form-control', 'id': 'district', 'placeholder': 'e.g: Kavrepalanchowk'}),
            'municipality': forms.Select(attrs={'class': 'form-control', 'id': 'municipality', 'placeholder': 'e.g: Budhanilkantha'}),
            'ward': forms.Select(attrs={'class': 'form-control', 'id': 'ward', 'placeholder': 'e.g: 1'}),
            'skill': forms.TextInput(attrs={'class': 'form-control','id':'skill', 'placeholder': 'Enter your Skills'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'experience'}),
            'citizenship_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citizenship_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'rate':forms.NumberInput(attrs={'class':'form-control',  'id':'rate', 'placeholder': 'Enter your rate per hour'})
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
                    raise forms.ValidationError("Select a valid ward number.")
            except Municipality.DoesNotExist:
                raise forms.ValidationError("Invalid municipality.")
        return ward

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
            'placeholder': 'Password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        password = cleaned_data.get('password')
        
        if phone_number and password:
            # Validate phone number format
            user = authenticate(phone_number=phone_number, password=password)
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
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'citizenship_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citizenship_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
