from rest_framework.generics import RetrieveAPIView
from common.djangoapps.edxmako.shortcuts import render_to_response

from django.http import HttpResponse
from django.template import loader
import requests

from cms.djangoapps.fx_programs.models import FxPrograms


def index(request):
    # if this is a POST request we need to process the form data
    for program in FxPrograms.objects.all():
        print(program.name)
        
    context = {
        'status': '200',
        'programs': FxPrograms.objects.all(),
    }
    response = render_to_response('programs_list.html', context)
    return response
 