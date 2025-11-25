import requests
from django.shortcuts import render

def public_programs(request):
    api_url = "https://discovery.unify.university/api/v1/programs/"
    programs = requests.get(api_url).json()
    return render(request, "public_programs/public_programs.html", {"programs": programs})
