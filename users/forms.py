# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, ManpowerProfile, Province, District, Municipality
from django.contrib.auth import get_user_model, authenticate

class UserSignupForm(UserCreationForm):
    username =  forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Username'}))
    
    phone_number = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Phone Number'}))


    class Meta:
        model = User
        fields = ('username', 'phone_number', 'password1', 'password2')

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class':'form-control', 'placeholder':'Password'})
        self.fields['password2'].widget.attrs.update({'class':'form-control', 'placeholder':'Confirm Password'})


    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if not phone.isdigit() or len(phone) < 10:
            raise forms.ValidationError("Enter a valid phone number (at least 10 digits).")
        return phone
    

class ManpowerSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Full Name'}))

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Email'}))

    province = forms.ChoiceField( required=True, label="Province", widget=forms.Select(attrs={
        'class': 'form-control', 
        'id' : 'province',
        'placeholder': "e.g: Bagmati"
    }))
    district = forms.ChoiceField(required=True, label="District",choices=[], widget=forms.Select(attrs={
        'class': 'form-control', 
        'id' : 'district',
        'placeholder': 'e.g: Kavrepalanchowk'}))
    
    municipality = forms.ChoiceField(required=True, label="Gaupalika/Nagarpalika",choices=[], widget=forms.Select(attrs={
        'placeholder': 'e.g. Budhanilkantha',
        'id' : 'municipality',
        'class': 'form-control'
    }))
    ward = forms.ChoiceField(required=True, label= "Ward No",choices=[], widget=forms.Select(attrs={
        'placeholder': 'e.g: 1',
        'id' : 'ward',
        'class': 'form-control'
    }))
   
    skill = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Skills'}))
    experience = forms.CharField(max_length=200, required=True, widget=forms.Textarea(attrs={
        'class': 'form-control', 'placeholder': 'experience'}))
    # photo = forms.ImageField(required=False, )
    citizenship_front = forms.ImageField(required=False)
    citizenship_back = forms.ImageField(required=False)
   
    def __init__(self, *args, **kwargs):
        super(ManpowerSignupForm, self).__init__(*args, **kwargs)
        self.fields['province'].choices = [('', '--- Select Province ---')]+ [(p.id, p.name) for p in Province.objects.all()]

        
    def clean_district(self):
        district_id = self.cleaned_data.get('district')
        if district_id and not District.objects.filter(id=district_id).exists():
            raise forms.ValidationError("Select a valid district.")
        return district_id

    def clean_municipality(self):
        municipality_id = self.cleaned_data.get('municipality')
        if municipality_id and not Municipality.objects.filter(id=municipality_id).exists():
            raise forms.ValidationError("Select a valid municipality.")
        return municipality_id

    def clean_ward(self):
        ward = self.cleaned_data.get('ward')
        municipality_id = self.cleaned_data.get('municipality')
        if ward and municipality_id:
            try:
                municipality = Municipality.objects.get(id=municipality_id)
                if int(ward) not in range(1, municipality.ward + 1):
                    raise forms.ValidationError("Select a valid ward number.")
            except Municipality.DoesNotExist:
                raise forms.ValidationError("Invalid municipality.")
        return ward

    class Meta:
        model = User
        fields = ( 'full_name','email','skill','province', 'district', 'municipality','ward', 'experience', 'citizenship_front', 'citizenship_back',
            
        )

    


User = get_user_model()
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
        cleaned_data =  super().clean()
        # email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
             try:
                 user = User.objects.get(username = username)
                 user = authenticate(username = user.username, password = password)
                 if user is None:
                     raise forms.ValidationError("Invalid credentials")
                 self.user = user
             except User.DoesNotExist:
                 raise forms.ValidationError("Invalid Credentials")
             
        return cleaned_data


class UserProfileUpdateForm(forms.ModelForm):
    user_type = 'user'

    class Meta:
        model = UserProfile  # or User if you're updating User model directly
        fields = ['username', 'phone_number']  # exclude user_type if not in model

class ManpowerProfileUpdateForm(forms.ModelForm):
    user_type = 'manpower'

    class Meta:
        model = ManpowerProfile  # use ManpowerProfile for manpower profile updates
        fields = ['skill', 'experience']  # exclude user_type if not in model


