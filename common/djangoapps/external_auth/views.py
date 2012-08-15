import functools
import json
import logging
import random
import re
import string

from external_auth.models import ExternalAuthMap

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from mitxmako.shortcuts import render_to_response, render_to_string
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    from django.contrib.csrf.middleware import csrf_exempt
from django_future.csrf import ensure_csrf_cookie
from util.cache import cache_if_anonymous
    
from django_openid_auth import auth as openid_auth
from openid.consumer.consumer import (Consumer, SUCCESS, CANCEL, FAILURE)
import django_openid_auth.views as openid_views

import student.views as student_views

log = logging.getLogger("mitx.external_auth")

@csrf_exempt
def default_render_failure(request, message, status=403, template_name='extauth_failure.html', exception=None):
    """Render an Openid error page to the user."""
    message = "In openid_failure " + message
    log.debug(message)
    data = render_to_string( template_name, dict(message=message, exception=exception))
    return HttpResponse(data, status=status)

#-----------------------------------------------------------------------------
# Openid

def edXauth_generate_password(length=12, chars=string.letters + string.digits):
    """Generate internal password for externally authenticated user"""
    return ''.join([random.choice(chars) for i in range(length)])

@csrf_exempt
def edXauth_openid_login_complete(request,  redirect_field_name=REDIRECT_FIELD_NAME, render_failure=None):
    """Complete the openid login process"""

    redirect_to = request.REQUEST.get(redirect_field_name, '')
    render_failure = render_failure or \
                     getattr(settings, 'OPENID_RENDER_FAILURE', None) or \
                     default_render_failure
                                                   
    openid_response = openid_views.parse_openid_response(request)
    if not openid_response:
        return render_failure(request, 'This is an OpenID relying party endpoint.')

    if openid_response.status == SUCCESS:
        external_id = openid_response.identity_url
        oid_backend =  openid_auth.OpenIDBackend()
        details = oid_backend._extract_user_details(openid_response)

        log.debug('openid success, details=%s' % details)

        return edXauth_external_login_or_signup(request,
                                                external_id, 
                                                "openid:%s" % settings.OPENID_SSO_SERVER_URL,
                                                details,
                                                details.get('email',''),
                                                '%s %s' % (details.get('first_name',''),details.get('last_name',''))
                                                )
                                 
    return render_failure(request, 'Openid failure')

#-----------------------------------------------------------------------------
# generic external auth login or signup

def edXauth_external_login_or_signup(request, external_id, external_domain, credentials, email, fullname,
                                     retfun=None):
    # see if we have a map from this external_id to an edX username
    try:
        eamap = ExternalAuthMap.objects.get(external_id = external_id,
                                            external_domain = external_domain,
                                            )
        log.debug('Found eamap=%s' % eamap)
    except ExternalAuthMap.DoesNotExist:
        # go render form for creating edX user
        eamap = ExternalAuthMap(external_id = external_id,
                                external_domain = external_domain,
                                external_credentials = json.dumps(credentials),
                                )
        eamap.external_email = email
        eamap.external_name = fullname
        eamap.internal_password = edXauth_generate_password()
        log.debug('created eamap=%s' % eamap)

        eamap.save()

    internal_user = eamap.user
    if internal_user is None:
        log.debug('ExtAuth: no user for %s yet, doing signup' % eamap.external_email)
        return edXauth_signup(request, eamap)
    
    uname = internal_user.username
    user = authenticate(username=uname, password=eamap.internal_password)
    if user is None:
        log.warning("External Auth Login failed for %s / %s" % (uname,eamap.internal_password))
        return edXauth_signup(request, eamap)

    if not user.is_active:
        log.warning("External Auth: user %s is not active" % (uname))
        # TODO: improve error page
        return render_failure(request, 'Account not yet activated: please look for link in your email')
     
    login(request, user)
    request.session.set_expiry(0)
    student_views.try_change_enrollment(request)
    log.info("Login success - {0} ({1})".format(user.username, user.email))
    if retfun is None:
        return redirect('/')
    return retfun()
        
    
#-----------------------------------------------------------------------------
# generic external auth signup

@ensure_csrf_cookie
@cache_if_anonymous
def edXauth_signup(request, eamap=None):
    """
    Present form to complete for signup via external authentication.
    Even though the user has external credentials, he/she still needs
    to create an account on the edX system, and fill in the user
    registration form.

    eamap is an ExteralAuthMap object, specifying the external user
    for which to complete the signup.
    """
    
    if eamap is None:
        pass

    request.session['ExternalAuthMap'] = eamap	# save this for use by student.views.create_account
    
    context = {'has_extauth_info': True,
               'show_signup_immediately' : True,
               'extauth_email': eamap.external_email,
               'extauth_username' : eamap.external_name.replace(' ',''), # default - conjoin name, no spaces
               'extauth_name': eamap.external_name,
               }
    
    log.debug('ExtAuth: doing signup for %s' % eamap.external_email)

    return student_views.main_index(request, extra_context=context)

#-----------------------------------------------------------------------------
# MIT SSL

def ssl_dn_extract_info(dn):
    '''
    Extract username, email address (may be anyuser@anydomain.com) and full name
    from the SSL DN string.  Return (user,email,fullname) if successful, and None
    otherwise.
    '''
    ss = re.search('/emailAddress=(.*)@([^/]+)', dn)
    if ss:
        user = ss.group(1)
        email = "%s@%s" % (user, ss.group(2))
    else:
        return None
    ss = re.search('/CN=([^/]+)/', dn)
    if ss:
        fullname = ss.group(1)
    else:
        return None
    return (user, email, fullname)

@csrf_exempt
def edXauth_ssl_login(request):
    """
    This is called by student.views.index when MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'] = True

    Used for MIT user authentication.  This presumes the web server (nginx) has been configured 
    to require specific client certificates.

    If the incoming protocol is HTTPS (SSL) then authenticate via client certificate.  
    The certificate provides user email and fullname; this populates the ExternalAuthMap.
    The user is nevertheless still asked to complete the edX signup.  

    Else continues on with student.views.main_index, and no authentication.
    """
    certkey = "SSL_CLIENT_S_DN"	 # specify the request.META field to use
    
    cert = request.META.get(certkey,'')
    if not cert:
        cert = request.META.get('HTTP_'+certkey,'')
    if not cert:
        try:
            cert = request._req.subprocess_env.get(certkey,'')	 # try the direct apache2 SSL key
        except Exception as err:
            pass
    if not cert:
        # no certificate information - go onward to main index
        return student_views.main_index(request)

    (user, email, fullname) = ssl_dn_extract_info(cert)
    
    return edXauth_external_login_or_signup(request, 
                                            external_id=email, 
                                            external_domain="ssl:MIT", 
                                            credentials=cert, 
                                            email=email,
                                            fullname=fullname,
                                            retfun = functools.partial(student_views.main_index, request))
