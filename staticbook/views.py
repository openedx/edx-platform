# Create your views here.
import os

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from djangomako.shortcuts import render_to_response, render_to_string

def index(request, page=0): 
    if not request.user.is_authenticated():
        return redirect('/')
    return render_to_response('staticbook.html',{'page':int(page)})

def index_shifted(request, page):
    return index(request, int(page)+24)
