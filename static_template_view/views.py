# View for semi-static templatized content. 
#
# List of valid templates is explicitly managed for (short-term)
# security reasons.

from djangomako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect

valid_templates=['index.html', 'staff.html', 'info.html', 'credits.html']

def index(request, template): 
    if template in valid_templates:
        return render_to_response(template,{})
    else:
        return redirect('/')
