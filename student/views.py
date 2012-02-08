import json
import logging
import random
import string

from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.validators import validate_email, validate_slug
from django.db import connection
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string

from models import Registration, UserProfile
from django_future.csrf import ensure_csrf_cookie

log = logging.getLogger("mitx.user")

def csrf_token(context):
    csrf_token = context.get('csrf_token', '')
    if csrf_token == 'NOTPROVIDED':
        return ''
    return u'<div style="display:none"><input type="hidden" name="csrfmiddlewaretoken" value="%s" /></div>' % (csrf_token)

@ensure_csrf_cookie
def index(request):
    if settings.COURSEWARE_ENABLED and request.user.is_authenticated():
        return redirect('/courseware')
    else:
        csrf_token = csrf(request)['csrf_token']
        # TODO: Clean up how 'error' is done. 
        return render_to_response('index.html', {'error' : '',
                                                 'csrf': csrf_token }) 
                                                 
# def courseinfo(request):
#     if request.user.is_authenticated():
#         return redirect('/courseware')
#     else:
#         csrf_token = csrf(request)['csrf_token']
#         # TODO: Clean up how 'error' is done. 
#         return render_to_response('courseinfo.html', {'error' : '',
#                                                  'csrf': csrf_token }) 

# Need different levels of logging
@ensure_csrf_cookie
def login_user(request, error=""):
    if 'email' not in request.POST or 'password' not in request.POST:
        return render_to_response('login.html', {'error':error.replace('+',' ')})

    email = request.POST['email']
    password = request.POST['password']
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        log.warning("Login failed - Unknown user email: {0}".format(email))
        return HttpResponse(json.dumps({'success':False, 
                                        'error': 'Invalid login'})) # TODO: User error message

    username = user.username
    user = authenticate(username=username, password=password)
    if user is None:
        log.warning("Login failed - password for {0} is invalid".format(email))
        return HttpResponse(json.dumps({'success':False, 
                                        'error': 'Invalid login'}))

    if user is not None and user.is_active:
        try:
            login(request, user)
            if request.POST['remember'] == 'true':
                request.session.set_expiry(None) # or change to 604800 for 7 days
                log.debug("Setting user session to never expire")
            else:
                request.session.set_expiry(0)
        except Exception as e:
            log.critical("Login failed - Could not create session. Is memcached running?")
            log.exception(e)

        log.info("Login success - {0} ({1})".format(username, email))
        return HttpResponse(json.dumps({'success':True}))

    log.warning("Login failed - Account not active for user {0}".format(username))
    return HttpResponse(json.dumps({'success':False, 
                                    'error': 'Account not active. Check your e-mail.'}))

@ensure_csrf_cookie
def logout_user(request):
    logout(request)
#    print len(connection.queries), connection.queries
    return redirect('/')

@ensure_csrf_cookie
def change_setting(request):
    if not request.user.is_authenticated():
        return redirect('/')
    up=UserProfile.objects.get(user=request.user)
    if 'location' in request.POST:
#        print "loc"
        up.location=request.POST['location']
    if 'language' in request.POST:
#        print "lang"
        up.language=request.POST['language']
    up.save()

    return HttpResponse(json.dumps({'success':True, 
                                    'language':up.language,
                                    'location':up.location,}))

@ensure_csrf_cookie
def create_account(request, post_override=None):
    js={'success':False}
    
    post_vars = post_override if post_override else request.POST
    
    # Confirm we have a properly formed request
    for a in ['username', 'email', 'password', 'location', 'language', 'name']:
        if a not in post_vars:
            js['value']="Error (401 {field}). E-mail us.".format(field=a)
            return HttpResponse(json.dumps(js))



    if post_vars['honor_code']!=u'true':
        js['value']="To enroll, you must follow the honor code.".format(field=a)
        return HttpResponse(json.dumps(js))


    if post_vars['terms_of_service']!=u'true':
        js['value']="You must accept the terms of service.".format(field=a)
        return HttpResponse(json.dumps(js))

    # Confirm appropriate fields are there. 
    # TODO: Check e-mail format is correct. 
    # TODO: Confirm e-mail is not from a generic domain (mailinator, etc.)? Not sure if 
    # this is a good idea
    # TODO: Check password is sane
    for a in ['username', 'email', 'password', 'terms_of_service', 'honor_code']:
        if len(post_vars[a])<2:
            js['value']="{field} is required.".format(field=a)
            return HttpResponse(json.dumps(js))

    try:
        validate_email(post_vars['email'])
    except:
        js['value']="Valid e-mail is required.".format(field=a)
        return HttpResponse(json.dumps(js))

    try:
        validate_slug(post_vars['username'])
    except:
        js['value']="Username should only consist of A-Z and 0-9.".format(field=a)
        return HttpResponse(json.dumps(js))
        
    

    # Confirm username and e-mail are unique. TODO: This should be in a transaction
    if len(User.objects.filter(username=post_vars['username']))>0:
        js['value']="An account with this username already exists."
        return HttpResponse(json.dumps(js))

    if len(User.objects.filter(email=post_vars['email']))>0:
        js['value']="An account with this e-mail already exists."
        return HttpResponse(json.dumps(js))

    u=User(username=post_vars['username'],
           email=post_vars['email'],
           is_active=False)
    u.set_password(post_vars['password'])
    r=Registration()
    # TODO: Rearrange so that if part of the process fails, the whole process fails. 
    # Right now, we can have e.g. no registration e-mail sent out and a zombie account
    u.save()
    r.register(u)

    up=UserProfile(user=u)
    up.name=post_vars['name']
    up.language=post_vars['language']
    up.location=post_vars['location']
    up.save()

    d={'name':post_vars['name'],
       'key':r.activation_key,
       'site':settings.SITE_NAME}

    subject = render_to_string('activation_email_subject.txt',d)
        # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string('activation_email.txt',d)

    try:
        if not settings.GENERATE_RANDOM_USER_CREDENTIALS:
            res=u.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    except:
        js['value']=str(sys.exc_info())
        return HttpResponse(json.dumps(js))
        
    js={'success':True,
        'value':render_to_string('registration/reg_complete.html', {'email':post_vars['email'], 
                                                                    'csrf':csrf(request)['csrf_token']})}
#    print len(connection.queries), connection.queries
    return HttpResponse(json.dumps(js), mimetype="application/json")
    
def create_random_account(create_account_function):
    
    def id_generator(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
    
    def inner_create_random_account(request):
        post_override= {'username' : "random_" + id_generator(),
                            'email' : id_generator(size=10, chars=string.ascii_lowercase) + "_dummy_test@mitx.mit.edu",
                            'password' : id_generator(),
                            'location' : id_generator(size=5, chars=string.ascii_uppercase),
                            'language' : id_generator(size=5, chars=string.ascii_uppercase) + "ish",
                            'name' : id_generator(size=5, chars=string.ascii_lowercase) + " " + id_generator(size=7, chars=string.ascii_lowercase),
                            'honor_code' : u'true',
                            'terms_of_service' : u'true',}
        
#        print "Creating random account: " , post_override
        
        return create_account_function(request, post_override = post_override)
        
    return inner_create_random_account

if settings.GENERATE_RANDOM_USER_CREDENTIALS:
    create_account = create_random_account(create_account)

@ensure_csrf_cookie
def activate_account(request, key):
    r=Registration.objects.filter(activation_key=key)
    if len(r)==1:
        if not r[0].user.is_active:
            r[0].activate()
            resp = render_to_response("activation_complete.html",{'csrf':csrf(request)['csrf_token']})
            return resp
        resp = render_to_response("activation_active.html",{'csrf':csrf(request)['csrf_token']})
        return resp
    if len(r)==0:
        return render_to_response("activation_invalid.html",{'csrf':csrf(request)['csrf_token']})
    return HttpResponse("Unknown error. Please e-mail us to let us know how it happened.")

@ensure_csrf_cookie
def password_reset(request):
    ''' Attempts to send a password reset e-mail. '''
    if request.method != "POST":
        raise Http404
    form = PasswordResetForm(request.POST)
    if form.is_valid():
        form.save( use_https = request.is_secure(),
                   from_email = settings.DEFAULT_FROM_EMAIL,
                   request = request )
        return HttpResponse(json.dumps({'success':True,
                                        'value': render_to_string('registration/password_reset_done.html', {})}))
    else:
        return HttpResponse(json.dumps({'success':False,
                                        'error': 'Invalid e-mail'}))
