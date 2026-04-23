import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model, authenticate
from .models import Province, District, Municipality, CustomUser, ManpowerProfile, Skill

User = get_user_model()

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s\-']{2,99}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_PATTERN = re.compile(r"^98\d{8}$")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


def _normalize_whitespace(value):
    return re.sub(r"\s+", " ", (value or "").strip())


def _normalize_phone(value):
    return re.sub(r"\s+", "", (value or "")).strip()


def _validate_person_name(value, field_name="Full name"):
    value = _normalize_whitespace(value)
    if not value:
        raise forms.ValidationError(f"{field_name} is required.")
    if not value[0].isalpha():
        raise forms.ValidationError(f"{field_name} must start with a letter.")
    if not NAME_PATTERN.fullmatch(value):
        raise forms.ValidationError(
            f"{field_name} can only contain letters, spaces, hyphens, and apostrophes."
        )

    # Require at least 3 alphabetic letters (not counting spaces/punctuation)
    letters_only = re.sub(r"[^A-Za-z]", "", value)
    if len(letters_only) < 3:
        raise forms.ValidationError(f"{field_name} must contain at least 3 letters.")
    return value


def _validate_email(value):
    email = (value or "").strip().lower()
    if not email:
        raise forms.ValidationError("Email is required.")
    if not email[0].isalpha():
        raise forms.ValidationError("Email must start with a letter.")
    if '@' not in email:
        raise forms.ValidationError("Please enter a valid email address.")

    local_part = email.split('@', 1)[0]
    if len(local_part) < 3:
        raise forms.ValidationError("Email username (before @) must be at least 3 characters.")
    if not EMAIL_PATTERN.fullmatch(email):
        raise forms.ValidationError("Please enter a valid email address.")
    return email


def _validate_phone_number(value, user_instance=None):
    phone = _normalize_phone(value)
    if not PHONE_PATTERN.fullmatch(phone):
        raise forms.ValidationError("Enter a valid 10-digit phone number starting with 98.")

    qs = CustomUser.objects.filter(phone_number=phone)
    if user_instance and user_instance.pk:
        qs = qs.exclude(pk=user_instance.pk)
    if qs.exists():
        raise forms.ValidationError("This phone number is already registered.")
    return phone


def _validate_image_upload(file_obj, field_label, required=False):
    if not file_obj:
        if required:
            raise forms.ValidationError(f"{field_label} is required.")
        return file_obj

    filename = getattr(file_obj, "name", "")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise forms.ValidationError(f"{field_label} must be an image file ({allowed}).")

    if getattr(file_obj, "size", 0) > MAX_IMAGE_SIZE_BYTES:
        raise forms.ValidationError(f"{field_label} size must not exceed 5MB.")

    content_type = getattr(file_obj, "content_type", "") or ""
    if content_type and not content_type.startswith("image/"):
        raise forms.ValidationError(f"{field_label} must be a valid image.")

    return file_obj


def _validate_location_hierarchy(province, district, municipality):
    province_exists = Province.objects.filter(name=province).exists()
    if not province_exists:
        raise forms.ValidationError({"province": "Select a valid province."})

    district_qs = District.objects.filter(name=district)
    if not district_qs.exists():
        raise forms.ValidationError({"district": "Select a valid district."})
    if not district_qs.filter(province__name=province).exists():
        raise forms.ValidationError({"district": "Selected district does not belong to the selected province."})

    municipality_qs = Municipality.objects.filter(name=municipality)
    if not municipality_qs.exists():
        raise forms.ValidationError({"municipality": "Select a valid municipality."})
    if not municipality_qs.filter(district__name=district).exists():
        raise forms.ValidationError({"municipality": "Selected municipality does not belong to the selected district."})


def _validate_rate_for_experience(experience, rate):
    if experience is None or rate is None:
        return

    if experience < 1 and not (0 <= rate <= 200):
        raise forms.ValidationError({"rate": "Rate must be between 0 and 200 for experience less than 1 year."})
    if 1 <= experience < 3 and not (0 <= rate <= 300):
        raise forms.ValidationError({"rate": "Rate must be between 0 and 300 for experience between 1 and 3 years."})
    if 3 <= experience < 5 and not (0 <= rate <= 400):
        raise forms.ValidationError({"rate": "Rate must be between 0 and 400 for experience between 3 and 5 years."})
    if experience >= 5 and not (0 <= rate <= 600):
        raise forms.ValidationError({"rate": "Rate must be between 0 and 600 for experience 5 years or more."})

class UserSignupForm(UserCreationForm):
    full_name = forms.CharField(min_length=3, max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name', 'minlength': '3'}))
    phone_number = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number', 'inputmode': 'numeric', 'pattern': '98[0-9]{8}'}))

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
        return _validate_person_name(self.cleaned_data.get('full_name'), field_name="Full name")

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
        return _validate_phone_number(self.cleaned_data.get('phone_number'))

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
        fields = ['email', 'skills', 'province', 'district', 'municipality', 'ward', 'experience', 'citizenship_front', 'citizenship_back', 'rate', 'about_yourself', 'latitude', 'longitude']
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
            'latitude': forms.HiddenInput(attrs={'id': 'latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'longitude'}),
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
        province = _normalize_whitespace(self.cleaned_data.get('province'))
        if province and not Province.objects.filter(name=province).exists():
            raise forms.ValidationError("Select a valid province.")
        return province

    def clean_district(self):
        district = _normalize_whitespace(self.cleaned_data.get('district'))
        if district and not District.objects.filter(name=district).exists():
            raise forms.ValidationError("Select a valid district.")
        return district

    def clean_municipality(self):
        municipality = _normalize_whitespace(self.cleaned_data.get('municipality'))
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
        email = _validate_email(self.cleaned_data.get('email'))
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_profile_picture(self):
        """Validate profile picture"""
        profile_picture = self.cleaned_data.get('profile_picture')
        return _validate_image_upload(profile_picture, "Profile photo", required=True)

    def clean_citizenship_front(self):
        return _validate_image_upload(self.cleaned_data.get('citizenship_front'), "Citizenship front image")

    def clean_citizenship_back(self):
        return _validate_image_upload(self.cleaned_data.get('citizenship_back'), "Citizenship back image")

    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        district = cleaned_data.get('district')
        municipality = cleaned_data.get('municipality')
        ward = cleaned_data.get('ward')
        experience = cleaned_data.get('experience')
        rate = cleaned_data.get('rate')

        if province and district and municipality:
            _validate_location_hierarchy(province, district, municipality)

        if ward is not None and municipality:
            try:
                municipality_obj = Municipality.objects.get(name=municipality, district__name=district)
                if int(ward) not in range(1, municipality_obj.ward + 1):
                    self.add_error('ward', f"Ward number must be between 1 and {municipality_obj.ward}.")
            except Municipality.DoesNotExist:
                # Handled by location hierarchy validation
                pass

        _validate_rate_for_experience(experience, rate)
        return cleaned_data

class LoginForm(forms.Form):
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number',
            'inputmode': 'numeric',
            'pattern': '98[0-9]{8}'
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
            normalized_phone = _normalize_phone(phone_number)
            cleaned_data['phone_number'] = normalized_phone

            if not PHONE_PATTERN.fullmatch(normalized_phone):
                raise forms.ValidationError("Enter a valid 10-digit phone number starting with 98.")

            user = authenticate(username=normalized_phone, password=password)
            if not user:
                raise forms.ValidationError("Phone number or password is incorrect.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            self.user = user
             
        return cleaned_data
    
class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone_number', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'minlength': '3'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'pattern': '98[0-9]{8}'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return phone
        return _validate_phone_number(phone, user_instance=self.instance)

    def clean_full_name(self):
        return _validate_person_name(self.cleaned_data.get('full_name'), field_name="Full name")
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = _validate_email(email)
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

    def clean_province(self):
        province = _normalize_whitespace(self.cleaned_data.get('province'))
        if province and not Province.objects.filter(name=province).exists():
            raise forms.ValidationError("Select a valid province.")
        return province

    def clean_district(self):
        district = _normalize_whitespace(self.cleaned_data.get('district'))
        if district and not District.objects.filter(name=district).exists():
            raise forms.ValidationError("Select a valid district.")
        return district

    def clean_municipality(self):
        municipality = _normalize_whitespace(self.cleaned_data.get('municipality'))
        if municipality and not Municipality.objects.filter(name=municipality).exists():
            raise forms.ValidationError("Select a valid municipality.")
        return municipality

    def clean_profile_picture(self):
        return _validate_image_upload(self.cleaned_data.get('profile_picture'), "Profile photo")

    def clean_citizenship_front(self):
        return _validate_image_upload(self.cleaned_data.get('citizenship_front'), "Citizenship front image")

    def clean_citizenship_back(self):
        return _validate_image_upload(self.cleaned_data.get('citizenship_back'), "Citizenship back image")

    def clean(self):
        cleaned_data = super().clean()
        province = cleaned_data.get('province')
        district = cleaned_data.get('district')
        municipality = cleaned_data.get('municipality')
        ward = cleaned_data.get('ward')
        experience = cleaned_data.get('experience')
        rate = cleaned_data.get('rate')

        if province and district and municipality:
            _validate_location_hierarchy(province, district, municipality)

        if ward is not None and municipality:
            try:
                municipality_obj = Municipality.objects.get(name=municipality, district__name=district)
                if int(ward) not in range(1, municipality_obj.ward + 1):
                    self.add_error('ward', f"Ward number must be between 1 and {municipality_obj.ward}.")
            except Municipality.DoesNotExist:
                pass

        _validate_rate_for_experience(experience, rate)
        return cleaned_data