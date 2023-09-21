"""
Helpers specific to these specific views.
Since many helper methods are shared between these views as well as views in the /api
and /rest_api folders, they live one level up in contentstore/helpers.py
"""
from django.http import HttpResponse


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)
