# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ManpowerProfile

class UserSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'phone_number', 'password1')

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number (at least 10 digits).")
        return phone
    

# List of all 77 districts of Nepal
DISTRICT_CHOICES = [
    ('Bhojpur', 'Bhojpur'),
    ('Dhankuta', 'Dhankuta'),
    ('Ilam', 'Ilam'),
    ('Jhapa', 'Jhapa'),
    ('Khotang', 'Khotang'),
    ('Morang', 'Morang'),
    ('Okhaldhunga', 'Okhaldhunga'),
    ('Panchthar', 'Panchthar'),
    ('Sankhuwasabha', 'Sankhuwasabha'),
    ('Solukhumbu', 'Solukhumbu'),
    ('Sunsari', 'Sunsari'),
    ('Taplejung', 'Taplejung'),
    ('Terhathum', 'Terhathum'),
    ('Udayapur', 'Udayapur'),
    ('Bara', 'Bara'),
    ('Parsa', 'Parsa'),
    ('Rautahat', 'Rautahat'),
    ('Saptari', 'Saptari'),
    ('Sarlahi', 'Sarlahi'),
    ('Siraha', 'Siraha'),
    ('Dhanusha', 'Dhanusha'),
    ('Mahottari', 'Mahottari'),
    ('Bhaktapur', 'Bhaktapur'),
    ('Kathmandu', 'Kathmandu'),
    ('Lalitpur', 'Lalitpur'),
    ('Chitwan', 'Chitwan'),
    ('Makwanpur', 'Makwanpur'),
    ('Ramechhap', 'Ramechhap'),
    ('Dolakha', 'Dolakha'),
    ('Sindhuli', 'Sindhuli'),
    ('Sindhupalchok', 'Sindhupalchok'),
    ('Kavrepalanchok', 'Kavrepalanchok'),
    ('Nuwakot', 'Nuwakot'),
    ('Rasuwa', 'Rasuwa'),
    ('Dhading', 'Dhading'),
    ('Gorkha', 'Gorkha'),
    ('Kaski', 'Kaski'),
    ('Lamjung', 'Lamjung'),
    ('Manang', 'Manang'),
    ('Mustang', 'Mustang'),
    ('Myagdi', 'Myagdi'),
    ('Nawalpur', 'Nawalpur'),
    ('Parbat', 'Parbat'),
    ('Syangja', 'Syangja'),
    ('Tanahun', 'Tanahun'),
    ('Baglung', 'Baglung'),
    ('Kapilvastu', 'Kapilvastu'),
    ('Palpa', 'Palpa'),
    ('Rupandehi', 'Rupandehi'),
    ('Arghakhanchi', 'Arghakhanchi'),
    ('Gulmi', 'Gulmi'),
    ('Dang', 'Dang'),
    ('Banke', 'Banke'),
    ('Bardiya', 'Bardiya'),
    ('Dailekh', 'Dailekh'),
    ('Dolpa', 'Dolpa'),
    ('Humla', 'Humla'),
    ('Jajarkot', 'Jajarkot'),
    ('Jumla', 'Jumla'),
    ('Kalikot', 'Kalikot'),
    ('Mugu', 'Mugu'),
    ('Rukum East', 'Rukum East'),
    ('Rukum West', 'Rukum West'),
    ('Salyan', 'Salyan'),
    ('Surkhet', 'Surkhet'),
    ('Achham', 'Achham'),
    ('Baitadi', 'Baitadi'),
    ('Bajhang', 'Bajhang'),
    ('Bajura', 'Bajura'),
    ('Dadeldhura', 'Dadeldhura'),
    ('Darchula', 'Darchula'),
    ('Doti', 'Doti'),
    ('Kanchanpur', 'Kanchanpur'),
    ('Kailali', 'Kailali'),
]

class ManpowerSignupForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, required=True, label="District")
    local_address = forms.CharField(max_length=100, required=True, label="Local Address", widget=forms.TextInput(attrs={
        'placeholder': 'e.g. Ward No. 5, Budhanilkantha',
        'class': 'form-control form-control-sm'
    }))
    phone = forms.CharField(max_length=15, required=True)
    skill = forms.CharField(max_length=100, required=True)
    experience_years = forms.IntegerField(min_value=0, required=True)
    photo = forms.ImageField(required=False)
    citizenship_front = forms.ImageField(required=False)
    citizenship_back = forms.ImageField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'name', 'district', 'local_address',
            'phone', 'skill', 'experience_years',
            'photo', 'citizenship_front', 'citizenship_back',
            
        )

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number (at least 10 digits).")
        return phone