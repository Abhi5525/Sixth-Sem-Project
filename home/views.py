from django.shortcuts import render
from users.models import ManpowerProfile
# from django.contrib.auth.models import User
from  django.views.generic.list import ListView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ManpowerSerializer

# Create your views here.
def home(request):
    query = request.GET.get('searchInput')
    if query:
        manpower_list = ManpowerProfile.objects.select_related('user').filter(
            skill__icontains=query
        ) | ManpowerProfile.objects.select_related('user').filter(
            user__full_name__icontains=query
        )
    else:
        manpower_list = ManpowerProfile.objects.all()
    return render(request, 'home/index.html', {
        'ManpowerList': manpower_list
    })

@api_view(['GET'])
def manpower_list_api(request):
    queryset = ManpowerProfile.objects.select_related('user').all()
    serializer = ManpowerSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def manpower_detail_api(request, pk):
    try:
        manpower = ManpowerProfile.objects.select_related('user').get(pk=pk)
    except ManpowerProfile.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    serializer = ManpowerSerializer(manpower)
    return Response(serializer.data)


