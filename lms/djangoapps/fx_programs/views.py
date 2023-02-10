from rest_framework.generics import RetrieveAPIView
from common.djangoapps.edxmako.shortcuts import render_to_response

from django.http import HttpResponse
from django.template import loader
import requests


def index(request):
    # if this is a POST request we need to process the form data
    context = {
        'status': '200'
    }
    response = render_to_response('programs_list.html', context)
    return response
