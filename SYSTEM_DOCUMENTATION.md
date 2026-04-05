# Service Manpower - Complete System Documentation
**Last Updated:** April 5, 2026  
**Status:** ✅ PRODUCTION READY

---

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Core Features](#core-features)
3. [Technical Architecture](#technical-architecture)
4. [Database Models](#database-models)
5. [Authentication & Security](#authentication--security)
6. [Form Validation](#form-validation)
7. [API Integration](#api-integration)
8. [UI/UX Features](#uiux-features)
9. [Admin Management](#admin-management)
10. [Deployment Guide](#deployment-guide)

---

## System Overview

**Service Manpower** is a location-based professional booking platform where clients can find and book trusted service professionals (plumbers, electricians, carpenters, etc.) for hourly work.

### Key Stakeholders
- **Clients**: Search and book professionals for services
- **Professionals**: Register, offer services, manage bookings, earn money
- **Admins**: Verify professionals, oversee bookings, manage system

### Technology Stack
- **Backend**: Django 5.1 with Python 3.x
- **Database**: PostgreSQL/SQLite
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript (Vanilla)
- **Maps**: Leaflet.js for location-based features
- **Payment**: eSewa integration
- **Authentication**: Phone-based (10-digit, starts with 98)

---

## Core Features

### ✅ User Authentication & Authorization
- **Phone-based Authentication**: 10-digit phone number (must start with 98 for Nepal)
- **Password Requirements**: Minimum 8 characters, must contain letters and numbers
- **User Types**: Client or Professional designation
- **Session Management**: Secure cookie-based sessions
- **JWT Support**: Token-based API authentication

### ✅ Professional Management
- **Multi-step Registration**: 4-step wizard (Personal → Location → Skills → KYC)
- **Live Camera KYC Capture**: Real-time camera access for profile photo verification
- **Verification Status**: PENDING → APPROVED → REJECTED workflow
- **Skills Management**: Select 1-3 skills from system categories
- **Experience Tracking**: Years of experience with rate validation
- **Location Services**: Province/District/Municipality/Ward hierarchy
- **Availability Toggle**: Real-time availability status management
- **Rating System**: 5-star ratings with review counts (realistic: 3.5-5.0 stars, 5-50 reviews per professional)

### ✅ Booking System
- **Professional Search**: By skill name with location-based sorting
- **Distance Calculation**: Real-time distance from user's GPS location
- **Real-time Filtering**: 
  - **Rating Slider**: Filter by minimum rating (0-5 stars)
  - **Price Filter**: Enter target price, shows professionals ±50% around that rate
- **Booking Process**: Date, time, duration selection
- **Overlap Prevention**: Prevents double-booking
- **30-minute Rule**: Minimum 30-minute advance booking required
- **Booking History**: Separate upcoming and past bookings
- **Status Tracking**: SCHEDULED → COMPLETED → CANCELLED

### ✅ Payment System
- **eSewa Integration**: Secure payment gateway
- **Deposit Model**: 10% deposit required upfront
- **Remaining Balance**: Due upon service completion
- **Transaction Tracking**: UUID-based transaction management
- **Payment Status**: Success/Failure handling with user feedback

### ✅ Location Management
- **Geographic Hierarchy**:
  - Provinces: Bagmati, Karnali, etc.
  - Districts: Kathmandu, Bhaktapur, etc.
  - Municipalities: Budhanilkantha, Tarakeshwar, etc.
  - Wards: 1-50 divisions per municipality
- **GPS Integration**: Browser geolocation for user positioning
- **Location Persistence**:
  - Clients: Session-based (localStorage)
  - Professionals: Database-stored (ManpowerProfile)
- **Distance Sorting**: Automatic sorting by proximity

### ✅ Rating & Review System
- **Post-Booking Reviews**: Collected after service completion
- **5-Star Rating**: Quantitative feedback
- **Written Comments**: Qualitative feedback
- **Automatic Averaging**: Signal-based calculation
- **Public Display**: Ratings shown on professional cards

---

## Technical Architecture

### Project Structure
```
Service_Manpower/
├── users/                    # User management & authentication
│   ├── models.py            # CustomUser, ManpowerProfile
│   ├── views.py             # Auth, profile, signup flows
│   ├── forms.py             # All form validation
│   ├── signals.py           # Auto-trigger actions (rating calc)
│   ├── tokens.py            # Password reset tokens
│   └── templates/
│       ├── signup.html      # Client registration
│       └── professional_signup.html  # 4-step pro registration
│
├── bookings/                # Booking management
│   ├── models.py            # Booking, RatingReview
│   ├── views.py             # Booking CRUD, payment logic
│   └── templates/
│       └── booking_form.html
│
├── home/                    # Landing & professional listings
│   ├── models.py            # Province, District, Municipality, Ward, Skill
│   ├── views.py             # Home page, professional search
│   ├── serializers.py       # API response formatting
│   └── templates/
│       └── index.html       # Main home page with search
│
├── adminpanel/              # Admin dashboard
│   ├── views.py             # Professional approval, user oversight
│   └── admin.py             # Django admin customization
│
└── Service_Manpower/        # Project settings
    ├── settings.py          # Django configuration
    ├── urls.py              # URL routing
    ├── wsgi.py
    └── asgi.py
```

### Core Models

#### CustomUser (users/models.py)
```python
- phone_number (USERNAME_FIELD, max 10 digits)
- full_name (required)
- email (unique, optional)
- is_client (boolean)
- is_professional (boolean)
- created_at (timestamp)
- latitude/longitude (for clients)
```

#### ManpowerProfile (users/models.py)
```python
- user (OneToOneField to CustomUser)
- skills (ManyToManyField to Skill)
- experience (years, 0-50)
- rate (hourly, NPR)
- verification_status (PENDING/APPROVED/REJECTED)
- rejection_reason (text, optional)
- is_available (boolean)
- average_rating (decimal, 0-5)
- total_reviews (integer)
- profile_picture (image, required)
- citizenship_front/back (image, required for KYC)
- province/district/municipality/ward (location hierarchy)
- about_yourself (biography text)
- latitude/longitude (GPS coordinates)
```

#### Booking (bookings/models.py)
```python
- client (ForeignKey to CustomUser)
- professional (ForeignKey to ManpowerProfile)
- date (date field)
- time (time field)
- end_time (calculated from duration)
- duration (decimal hours, 0.5 minimum)
- status (SCHEDULED/COMPLETED/CANCELLED)
- created_at (timestamp)
```

#### RatingReview (bookings/models.py)
```python
- professional (ForeignKey to ManpowerProfile)
- reviewer (ForeignKey to CustomUser)
- rating (1-5 stars)
- comment (optional text)
- created_at (timestamp)
```

#### Skill (home/models.py)
```python
- name (skill category)
- category (grouping)
```

#### Geographic Models (home/models.py)
```python
- Province: name
- District: name, province (FK)
- Municipality: name, district (FK), ward (max ward number)
- Ward: number, municipality (FK)
```

---

## Authentication & Security

### ✅ User Authentication
- **Phone-based Login**: Unique 10-digit phone number (starts with 98)
- **Password Hashing**: Django's PBKDF2 by default
- **Session Management**: Django sessions framework
- **Login Required**: @login_required decorators on sensitive views
- **CSRF Protection**: {% csrf_token %} on all forms

### ✅ Authorization
- **Client-only Views**: Professional listing, booking creation
- **Professional-only Views**: Profile update, availability toggle, dashboard
- **Admin-only Views**: Professional approval, user management
- **Ownership Verification**: Users can only access/modify their own data

### ✅ Data Validation

#### Phone Number Validation
- Exactly 10 digits
- Must start with 98 (Nepal country code)
- Must be unique
- No special characters

#### Password Validation
- Minimum 8 characters
- Must contain letters (A-Z, a-z)
- Must contain numbers (0-9)
- Case-sensitive

#### Name Validation
- Cannot start with a number
- Must start with a letter
- Only letters, spaces, hyphens, apostrophes

#### Rate Validation (Experience-based)
- 0-1 years: max ₹200/hour
- 1-3 years: max ₹300/hour
- 3-5 years: max ₹400/hour
- 5+ years: max ₹600/hour

#### Booking Validation
- Minimum 30 minutes advance booking
- No past-date bookings
- No overlapping bookings for same professional
- Duration minimum 0.5 hours (30 minutes)
- Duration step 0.5 hours

#### Email Validation
- Standard email format
- Cannot start with number
- Must be unique

---

## Form Validation

### UserSignupForm (Client Registration)
```
ServerSide:
  - full_name: 100 chars max, no numbers at start
  - phone_number: 10 digits, starts with 98, unique
  - password1: 8+ chars, letters+numbers minimum
  - password2: must match password1

ClientSide:
  - All fields required
  - Real-time phone validation
  - Password strength meter
```

### ManpowerSignupForm (Professional Registration)
```
Step 1 - Personal Information:
  - email: valid format, unique
  - rate: 0 < rate <= 10000
  - about_yourself: text description

Step 2 - Location:
  - province: must exist in DB
  - district: must exist for selected province
  - municipality: must exist for selected district
  - ward: must be in valid range (1 to municipality.max_wards)

Step 3 - Skills:
  - skills: select 1-3 skills minimum
  - experience: 0-50 years

Step 4 - KYC:
  - citizenship_front: image file required
  - citizenship_back: image file required
  - profile_picture: camera capture required (KYC-style)
```

### LoginForm
```
- phone_number: required, 10 digits
- password: required, 8+ chars
- Custom authentication using phone+password
```

---

## API Integration

### eSewa Payment Gateway
```
Endpoint: https://eSewa.com.np/api/epay/...
Flow:
  1. Calculate 10% of booking amount
  2. Create transaction with unique UUID
  3. Redirect to eSewa payment page
  4. eSewa verifies & redirects back
  5. Verify signature & update booking status
```

### Location-Based APIs
```
JavaScript Geolocation API:
  - navigator.geolocation.getCurrentPosition()
  - Returns: latitude, longitude
  - Stored: localStorage (client), database (professional)

Leaflet.js Map API:
  - Interactive map display
  - Marker positioning
  - Distance calculation
```

---

## UI/UX Features

### Home Page (index.html)
```
Components:
  - Hero section with CTA
  - Professional search bar (compact search button)
  - Filter modal:
    * Price input field (show ±50% range by input value)
    * Rating slider (0-5 stars with dynamic star display)
    * Real-time result updates
    * Filter stats showing match count
  
  - Professional cards (responsive grid):
    * Profile picture
    * Professional name & skills
    * Rating (★ X.X, Y reviews)
    * Distance from user (km)
    * Hourly rate (₹/hour clearly labeled)
    * Availability status badge
    * Quick book button
```

### Professional Signup (professional_signup.html)
```
Layout:
  - Split-screen design (gradient left panel + form right)
  - 4-step progress bar with status indicators
  - Multi-step form wizard
  - Back/Next navigation

Styling:
  - Clean black labels (always visible)
  - Icons left-aligned in input fields
  - Consistent padding/spacing
  - Responsive (stacks on mobile)
  - Field icons with proper positioning
  - Error handling with visual feedback

Steps:
  1. Personal: Email, Rate, About Yourself
  2. Location: Province, District, Municipality, Ward (2-column grid)
  3. Skills: Skill search + selection (1-3 skills)
  4. KYC: Citizenship docs + Camera capture + Success message
```

### Client Signup (signup.html)
```
Layout:
  - Single-page form
  - Floating label animations
  - Password strength indicator
  - Social login options (styled)
  - Terms & conditions checkbox

Fields:
  - Full Name
  - Phone Number (10 digits)
  - Email
  - Password (with visibility toggle)
  - Confirm Password
  - Accept Terms checkbox
```

---

## Admin Management

### Admin Panel (adminpanel/)
```
Features:
  - Professional verification dashboard
  - User management
  - Booking oversight
  - Professional approval/rejection with reason
  - Rejection reason notification to user
  - View all bookings with status
  - View all payments with status
```

### Django Admin Interface
```
Models Accessible:
  - CustomUser: View/edit all users
  - ManpowerProfile: View/edit professionals
  - Booking: View all bookings
  - RatingReview: View all reviews
  - Province/District/Municipality/Ward: Manage locations
  - Skill: Manage skill categories
```

---

## Deployment Guide

### Environment Setup
```bash
# Clone repository
git clone <repo-url>
cd Service_Manpower

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirement.txt

# Create .env file
echo SECRET_KEY=your-secret-key >> .env
echo DEBUG=False >> .env
echo ALLOWED_HOSTS=your-domain.com >> .env
```

### Database Migration
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Load location data (provinces, districts, etc.)
python manage.py loaddata location_data.json  # or use DataOfLocalBody/loadData.py
```

### Static Files & Media
```bash
# Collect static files
python manage.py collectstatic --noinput

# Ensure media folder has proper permissions
chmod -R 755 media/
```

### Running Development Server
```bash
python manage.py runserver
# Access at http://localhost:8000
```

### Production Deployment
```
Server: Ubuntu 20.04 LTS
Web Server: Nginx
App Server: Gunicorn
Database: PostgreSQL
SSL: Let's Encrypt

Process:
1. Set DEBUG=False in settings.py
2. Configure ALLOWED_HOSTS with your domain
3. Use PostgreSQL instead of SQLite
4. Configure eSewa in production mode
5. Set up SSL certificates
6. Configure Gunicorn & Nginx
7. Enable CSRF cookie security settings
```

---

## Key Files Reference

### Authentication (users/)
- `users/views.py`: signup, login, logout, profile management
- `users/forms.py`: All form validation logic
- `users/models.py`: CustomUser, ManpowerProfile definitions
- `users/signals.py`: Auto-calculate ratings on review creation

### Bookings (bookings/)
- `bookings/views.py`: Booking creation, eSewa payment flow
- `bookings/models.py`: Booking, RatingReview models
- `bookings/templates/booking_form.html`: Booking form with validation

### Home & Listings (home/)
- `home/views.py`: Professional listing, search filtering
- `home/models.py`: Province, District, Municipality, Ward, Skill
- `home/templates/index.html`: Main page with filter modal
- `home/static/home/css/index.css`: Filter styling, responsive design

### Static Files
- `users/static/users/css/signup.css`: Pristine client signup styling
- `users/static/users/css/prosignup.css`: Professional signup styling (clean labels)
- `users/static/users/js/camera-capture.js`: KYC camera integration
- `home/static/home/css/index.css`: Filter system, professional cards

---

## Testing Credentials

### Sample Users
**Normal Clients:**
- Phone: 9851234567 | Phone: 9861234567 | Phone: 9871234567

**Professionals (Verified):**
- 16 total in system with realistic ratings (3.5-5.0 stars)
- Skills: Plumbing, Carpentry, Electricity, Painting
- Location: Primarily Bagmati Province

**Admin Access:**
- Use Django admin at /admin/ with superuser account

---

## Current Status Summary

### ✅ Completed Features
- ✅ Phone-based authentication (10-digit validation)
- ✅ Professional signup with 4-step wizard
- ✅ Live camera KYC capture
- ✅ Professional verification workflow (PENDING/APPROVED/REJECTED)
- ✅ Professional database (16 professionals, realistic ratings)
- ✅ Real-time professional search & filtering
- ✅ Price filter (type price, see ±50% range)
- ✅ Rating slider filter (0-5 stars)
- ✅ Location-based distance sorting
- ✅ Booking system with overlap prevention
- ✅ eSewa payment integration
- ✅ Rating & review system
- ✅ Admin professional approval/rejection
- ✅ Clean, centered signup styling
- ✅ Professional signup form validation
- ✅ All form labels visible and black
- ✅ Icon placement properly aligned
- ✅ Responsive design (mobile-friendly)

### 🎯 System Ready For
- Production deployment
- User engagement
- Professional growth
- Revenue generation via eSewa payments
- Admin oversight and quality control

---

## Support & Troubleshooting

### Common Issues
1. **Location not detected**: Check browser geolocation permissions
2. **Professional not appearing**: Check verification_status (must be APPROVED and is_available=True)
3. **Payment failing**: Verify eSewa credentials in .env
4. **Booking overlap error**: Check existing bookings for the time slot

### Contact
- Admin: Access Django admin at /admin/
- Support: Check rejection reasons in user alerts
- Logs: Check Django development server output

---

**System Version:** 1.0.0  
**Last Updated:** April 5, 2026  
**Maintained By:** Development Team
