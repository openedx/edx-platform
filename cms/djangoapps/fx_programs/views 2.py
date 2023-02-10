from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core import serializers
import numpy as np
from .models import FxPrograms
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from common.djangoapps.edxmako.shortcuts import render_to_response
from django.http import JsonResponse


@require_GET
@login_required
def index(request):

    context = {
        'email': request.user.email,
        'programs': FxPrograms.objects.all()
    }
    response = render_to_response('fx_programs_form.html', context)
    return response
