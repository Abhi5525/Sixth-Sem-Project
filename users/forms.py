# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, ManpowerProfile
from django.contrib.auth import get_user_model, authenticate

class UserSignupForm(UserCreationForm):
    username = None
    full_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Full Name'}))

    phone_number = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Phone Number'}))

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control','placeholder': 'Email Address'
    }))

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone_number', 'password1', 'password2')

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class':'form-control', 'placeholder':'Password'})
        self.fields['password2'].widget.attrs.update({'class':'form-control', 'placeholder':'Confirm Password'})


    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number (at least 10 digits).")
        return phone
    
User = get_user_model()
class LoginForm(forms.Form):
    username = None
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control','placeholder': 'Email Address'
    }))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'form-control','placeholder': 'Password'
    }))
    
    def clean(self):
        cleaned_data =  super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
             try:
                 user = User.objects.get(email = email)
                 user = authenticate(username = user.username, password = password)
                 if user is None:
                     raise forms.ValidationError("Invalid credentials")
                 self.user = user
             except User.DoesNotExist:
                 raise forms.ValidationError("Invalid Credentials")
             
        return cleaned_data


class ManpowerSignupForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    district = forms.CharField(max_length=100, required=True, label="District", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}))
    local_address = forms.CharField(max_length=100, required=True, label="Local Address", widget=forms.TextInput(attrs={
        'placeholder': 'e.g. Ward No. 5, Budhanilkantha',
        'class': 'form-control'
    }))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}))
    skill = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skills'}))
    experience_years = forms.IntegerField(min_value=0, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'experience'}))
    photo = forms.ImageField(required=False, )
    citizenship_front = forms.ImageField(required=False)
    citizenship_back = forms.ImageField(required=False)
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))

    class Meta:
        model = User
        fields = (
             'email', 'name', 
            'phone', 'skill', 'district', 'local_address','experience_years',
            'photo', 'citizenship_front', 'citizenship_back',
            
        )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number (at least 10 digits).")
        return phone

    

# # List of all 77 districts of Nepal
# DISTRICT_CHOICES = [
#     ('Bhojpur', 'Bhojpur'),
#     ('Dhankuta', 'Dhankuta'),
#     ('Ilam', 'Ilam'),
#     ('Jhapa', 'Jhapa'),
#     ('Khotang', 'Khotang'),
#     ('Morang', 'Morang'),
#     ('Okhaldhunga', 'Okhaldhunga'),
#     ('Panchthar', 'Panchthar'),
#     ('Sankhuwasabha', 'Sankhuwasabha'),
#     ('Solukhumbu', 'Solukhumbu'),
#     ('Sunsari', 'Sunsari'),
#     ('Taplejung', 'Taplejung'),
#     ('Terhathum', 'Terhathum'),
#     ('Udayapur', 'Udayapur'),
#     ('Bara', 'Bara'),
#     ('Parsa', 'Parsa'),
#     ('Rautahat', 'Rautahat'),
#     ('Saptari', 'Saptari'),
#     ('Sarlahi', 'Sarlahi'),
#     ('Siraha', 'Siraha'),
#     ('Dhanusha', 'Dhanusha'),
#     ('Mahottari', 'Mahottari'),
#     ('Bhaktapur', 'Bhaktapur'),
#     ('Kathmandu', 'Kathmandu'),
#     ('Lalitpur', 'Lalitpur'),
#     ('Chitwan', 'Chitwan'),
#     ('Makwanpur', 'Makwanpur'),
#     ('Ramechhap', 'Ramechhap'),
#     ('Dolakha', 'Dolakha'),
#     ('Sindhuli', 'Sindhuli'),
#     ('Sindhupalchok', 'Sindhupalchok'),
#     ('Kavrepalanchok', 'Kavrepalanchok'),
#     ('Nuwakot', 'Nuwakot'),
#     ('Rasuwa', 'Rasuwa'),
#     ('Dhading', 'Dhading'),
#     ('Gorkha', 'Gorkha'),
#     ('Kaski', 'Kaski'),
#     ('Lamjung', 'Lamjung'),
#     ('Manang', 'Manang'),
#     ('Mustang', 'Mustang'),
#     ('Myagdi', 'Myagdi'),
#     ('Nawalpur', 'Nawalpur'),
#     ('Parbat', 'Parbat'),
#     ('Syangja', 'Syangja'),
#     ('Tanahun', 'Tanahun'),
#     ('Baglung', 'Baglung'),
#     ('Kapilvastu', 'Kapilvastu'),
#     ('Palpa', 'Palpa'),
#     ('Rupandehi', 'Rupandehi'),
#     ('Arghakhanchi', 'Arghakhanchi'),
#     ('Gulmi', 'Gulmi'),
#     ('Dang', 'Dang'),
#     ('Banke', 'Banke'),
#     ('Bardiya', 'Bardiya'),
#     ('Dailekh', 'Dailekh'),
#     ('Dolpa', 'Dolpa'),
#     ('Humla', 'Humla'),
#     ('Jajarkot', 'Jajarkot'),
#     ('Jumla', 'Jumla'),
#     ('Kalikot', 'Kalikot'),
#     ('Mugu', 'Mugu'),
#     ('Rukum East', 'Rukum East'),
#     ('Rukum West', 'Rukum West'),
#     ('Salyan', 'Salyan'),
#     ('Surkhet', 'Surkhet'),
#     ('Achham', 'Achham'),
#     ('Baitadi', 'Baitadi'),
#     ('Bajhang', 'Bajhang'),
#     ('Bajura', 'Bajura'),
#     ('Dadeldhura', 'Dadeldhura'),
#     ('Darchula', 'Darchula'),
#     ('Doti', 'Doti'),
#     ('Kanchanpur', 'Kanchanpur'),
#     ('Kailali', 'Kailali'),
# ]
