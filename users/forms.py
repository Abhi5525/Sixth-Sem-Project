import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model, authenticate
from .models import Province, District, Municipality, CustomUser, ManpowerProfile, Skill

User = get_user_model()

class UserSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    phone_number = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))

    class Meta:
        model = CustomUser
        fields = ('full_name', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'usable_password' in self.fields:
            self.fields.pop('usable_password')
        self.fields['password1'].widget.attrs.update({'class': 'form-control','id': 'password1', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control','id': 'password2', 'placeholder': 'Confirm Password'})

    def clean_full_name(self):
        """Validate full name: cannot start with number, must contain only letters and spaces"""
        full_name = self.cleaned_data.get('full_name')
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        
        # Cannot start with a digit
        if full_name[0].isdigit():
            raise forms.ValidationError("Full name cannot start with a number.")
        
        # Cannot start with special characters
        if not full_name[0].isalpha():
            raise forms.ValidationError("Full name must start with a letter.")
        
        # Only letters, spaces, and hyphens allowed
        if not re.match(r"^[a-zA-Z\s\-']{2,100}$", full_name):
            raise forms.ValidationError("Full name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return full_name

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
        phone = re.sub(r'\s+', '', phone)
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Enter a valid phone number (10 digits).")
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

class ManpowerSignupForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all().order_by('category', 'name'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'skills-checkbox',
            'data-form-type': 'signup'
        }),
        required=True,
        help_text="Select at least one skill. Maximum 3 skills allowed."
    )
    
    profile_picture = forms.ImageField(
        required=True,
        label='Profile Photo (KYC Verification)',
        widget=forms.FileInput(attrs={
            'class': 'd-none',
            'id': 'profile_picture',
            'accept': 'image/*',
            'style': 'display: none !important;',
        }),
        help_text="Capture a photo using camera for identity verification (KYC)."
    )

    class Meta:
        model = ManpowerProfile
        fields = ['email', 'skills', 'province', 'district', 'municipality', 'ward', 'experience', 'citizenship_front', 'citizenship_back', 'rate', 'about_yourself']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'email'}),
            'province': forms.Select(attrs={'class': 'form-control', 'id': 'province'}),
            'district': forms.Select(attrs={'class': 'form-control', 'id': 'district'}),
            'municipality': forms.Select(attrs={'class': 'form-control', 'id': 'municipality'}),
            'ward': forms.Select(attrs={'class': 'form-control', 'id': 'ward'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'citizenship_front': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'citizenship_back': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'id': 'rate'}),
            'about_yourself': forms.Textarea(attrs={'class': 'form-control'}),
        }
        labels = {
            'rate': 'Rate/Hour',
            'skills': 'Professional Skills',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['province'].widget.choices = [('', '--- Select Province ---')] + [(p.name, p.name) for p in Province.objects.all()]
    
    def save(self, commit=True):
        """Override save to handle profile_picture field"""
        instance = super().save(commit=False)
        
        # Set profile picture from form
        if 'profile_picture' in self.cleaned_data:
            instance.profile_picture = self.cleaned_data['profile_picture']
        
        if commit:
            instance.save()
        
        return instance

    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if not skills:
            raise forms.ValidationError("You must select at least one skill.")
        if skills.count() > 3:
            raise forms.ValidationError("You can select a maximum of 3 skills.")
        return skills

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
        if not email:
            raise forms.ValidationError("Email is required.")
        
        # Email cannot start with a digit
        if email[0].isdigit():
            raise forms.ValidationError("Email cannot start with a number.")
        
        # Email format validation (RFC 5322 simplified)
        email_pattern = r"^[a-zA-Z][a-zA-Z0-9._%-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise forms.ValidationError("Please enter a valid email address (must start with a letter).")
        
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_profile_picture(self):
        """Validate profile picture"""
        profile_picture = self.cleaned_data.get('profile_picture')
        if not profile_picture:
            raise forms.ValidationError("Profile photo is required for identity verification.")
        
        # Check file size (max 5MB)
        if profile_picture.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Image size must not exceed 5MB.")
        
        return profile_picture

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
            normalized_phone = re.sub(r'\s+', '', phone_number).strip()
            cleaned_data['phone_number'] = normalized_phone

            if not normalized_phone.isdigit() or len(normalized_phone) != 10:
                raise forms.ValidationError("Enter a valid 10-digit phone number.")

            try:
                user = authenticate(username=normalized_phone, password=password)
                if not user:
                    raise forms.ValidationError("Phone number or password is incorrect.")
                if not user.is_active:
                    raise forms.ValidationError("This account has been deactivated.")
                self.user = user
            except Exception as e:
                raise forms.ValidationError(f"Login error: {str(e)}")
             
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
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all().order_by('category', 'name'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'skills-checkbox',
            'data-form-type': 'update'
        }),
        required=True,
        help_text="Select at least one skill. Maximum 3 skills allowed."
    )

    class Meta:
        model = ManpowerProfile
        fields = [
            'skills', 'province', 'district', 'municipality', 'ward',
            'experience', 'citizenship_front', 'citizenship_back', 'rate',
            'profile_picture'
        ]
        widgets = {
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
        labels = {
            'skills': 'Professional Skills',
        }

    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if not skills:
            raise forms.ValidationError("You must select at least one skill.")
        if skills.count() > 3:
            raise forms.ValidationError("You can select a maximum of 3 skills.")
        return skills
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