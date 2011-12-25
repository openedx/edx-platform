from djangomako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect
import os
from django.conf import settings
from django.http import Http404

# We don't do subdirectories to reduce odds of possible future
# security issues. Feel free to re-add them if needed -- just make
# sure things like /../../etc/passwd are handled okay. 

valid_files=os.listdir(settings.TEXTBOOK_DIR)

def index(request, filename): 
    if filename in valid_files:
        text=open(settings.TEXTBOOK_DIR+filename).read()
        return render_to_response('textbook.html',{'text':text})
    else:
        raise Http404
