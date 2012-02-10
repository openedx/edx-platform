# View for semi-static templatized content. 
#
# List of valid templates is explicitly managed for (short-term)
# security reasons.

from mitxmako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect
from django.core.context_processors import csrf
from django.conf import settings

#valid_templates=['index.html', 'staff.html', 'info.html', 'credits.html']
valid_templates=['index.html', 
                 'tos.html', 
                 'privacy.html', 
                 'honor.html', 
                 'copyright.html', 
                 '404.html']

print "!!",settings.__dict__

if settings.STATIC_GRAB: 
    valid_templates = valid_templates+['server-down.html',
                                       'server-error.html'
                                       'server-overloaded.html', 
                                       'mitx_global.html', 
                                       'mitx-overview.html', 
                                       '6002x-faq.html',
                                       '6002x-press-release.html'
                                       ]

def index(request, template): 
    csrf_token = csrf(request)['csrf_token']
    if template in valid_templates:
        return render_to_response(template, {'error' : '',
                                             'csrf': csrf_token }) 
    else:
        return redirect('/')

valid_auth_templates=['help.html']

def auth_index(request, template): 
    if not request.user.is_authenticated():
        return redirect('/')

    if template in valid_auth_templates:
        return render_to_response(template,{})
    else:
        return redirect('/')
