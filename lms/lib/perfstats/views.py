# Create your views here.
import middleware

from django.http import HttpResponse


def end_profile(request):
    names = middleware.restart_profile()
    return HttpResponse(str(names))
