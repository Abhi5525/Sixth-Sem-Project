from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ManpowerProfile, Province, District, Municipality
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class UserSignupForm(UserCreationForm):
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    phone_number = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))

    class Meta:
        model = User
        fields = ('username', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm Password'})

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number (at least 10 digits).")
        return phone

class ManpowerSignupForm(forms.ModelForm):
    class Meta:
        model = ManpowerProfile
        fields = ['full_name', 'email', 'skill', 'province', 'district', 'municipality', 'ward', 'experience', 'citizenship_front', 'citizenship_back']
        widgets = {
            'province': forms.Select(attrs={'class': 'form-control', 'id': 'province', 'placeholder': "e.g: Bagmati"}),
            'district': forms.Select(attrs={'class': 'form-control', 'id': 'district', 'placeholder': 'e.g: Kavrepalanchowk'}),
            'municipality': forms.Select(attrs={'class': 'form-control', 'id': 'municipality', 'placeholder': 'e.g: Budhanilkantha'}),
            'ward': forms.Select(attrs={'class': 'form-control', 'id': 'ward', 'placeholder': 'e.g: 1'}),
            'skill': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skills'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'experience'}),
            'citizenship_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citizenship_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the logged-in user from kwargs
        super(ManpowerSignupForm, self).__init__(*args, **kwargs)
        if user:
            try:
                user_profile = UserProfile.objects.get(user=user)
                # Pre-fill fields from UserProfile or User
                self.fields['full_name'].initial = user_profile.username  # or user.get_full_name()
                self.fields['email'].initial = user.email
            except UserProfile.DoesNotExist:
                self.fields['full_name'].initial = user.username
                self.fields['email'].initial = user.email
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
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
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
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            try:
                user = User.objects.get(username=username)
                user = authenticate(username=user.username, password=password)
                if user is None:
                    raise forms.ValidationError("Invalid credentials")
                self.user = user
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid Credentials")
             
        return cleaned_data

class UserProfileUpdateForm(forms.ModelForm):
    user_type = 'user'

    class Meta:
        model = UserProfile
        fields = ['username', 'phone_number']

class ManpowerProfileUpdateForm(forms.ModelForm):
    user_type = 'manpower'

    class Meta:
        model = ManpowerProfile
        fields = ['skill', 'experience']