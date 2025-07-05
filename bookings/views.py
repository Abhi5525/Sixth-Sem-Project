from django.shortcuts import render

# Create your views here.

def bookings(request):
    return render(request, 'bookings/bookings.html')

def detailsForm(request):
    return render(request, 'bookings/detailsForm.html')
