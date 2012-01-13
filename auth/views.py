from djangomako.shortcuts import render_to_response, render_to_string
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse
import json
from models import Registration, UserProfile
from django.conf import settings
from django.core.context_processors import csrf
from django.core.validators import validate_email, validate_slug

def csrf_token(context):
    csrf_token = context.get('csrf_token', '')
    if csrf_token == 'NOTPROVIDED':
        return ''
    return u'<div style="display:none"><input type="hidden" name="csrfmiddlewaretoken" value="%s" /></div>' % (csrf_token)


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

def login_user(request, error=""):
    print request.POST
    if 'email' not in request.POST or 'password' not in request.POST:
        print "X"
        return render_to_response('login.html', {'error':error.replace('+',' ')})
    email = request.POST['email']
    password = request.POST['password']
    try:
        user=User.objects.get(email=email)
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'success':False, 
                                        'error': 'Invalid login'})) # TODO: User error message

    username=user.username
    user=authenticate(username=username, password=password)
    if user is None:
        return HttpResponse(json.dumps({'success':False, 
                                        'error': 'Invalid login'}))
    if user is not None and user.is_active:
        login(request, user)
        if request.POST['remember'] == 'true':
            request.session.set_expiry(None) # or change to 604800 for 7 days
            print "recall"
        else:
            request.session.set_expiry(0)
        print "close"


        return HttpResponse(json.dumps({'success':True}))

    return HttpResponse(json.dumps({'success':False, 
                                    'error': 'Account not active. Check your e-mail.'}))

def logout_user(request):
    logout(request)
    return redirect('/')

def change_setting(request):
    if not request.user.is_authenticated():
        return redirect('/')
    up=UserProfile.objects.get(user=request.user)
    if 'location' in request.POST:
        print "loc"
        up.location=request.POST['location']
    if 'language' in request.POST:
        print "lang"
        up.language=request.POST['language']
    up.save()

    return HttpResponse(json.dumps({'success':True, 
                                    'language':up.language,
                                    'location':up.location,}))

def create_account(request):
    js={'success':False}
    # Confirm we have a properly formed request
    for a in ['username', 'email', 'password', 'location', 'language', 'name']:
        if a not in request.POST:
            js['value']="Error (401 {field}). E-mail us.".format(field=a)
            return HttpResponse(json.dumps(js))



    if request.POST['honor_code']!=u'true':
        js['value']="To enroll, you must follow the honor code.".format(field=a)
        return HttpResponse(json.dumps(js))


    if request.POST['terms_of_service']!=u'true':
        js['value']="You must accept the terms of service.".format(field=a)
        return HttpResponse(json.dumps(js))

    # Confirm appropriate fields are there. 
    # TODO: Check e-mail format is correct. 
    # TODO: Confirm e-mail is not from a generic domain (mailinator, etc.)? Not sure if 
    # this is a good idea
    # TODO: Check password is sane
    for a in ['username', 'email', 'password', 'terms_of_service', 'honor_code']:
        if len(request.POST[a])<2:
            js['value']="{field} is required.".format(field=a)
            return HttpResponse(json.dumps(js))

    try:
        validate_email(request.POST['email'])
    except:
        js['value']="Valid e-mail is required.".format(field=a)
        return HttpResponse(json.dumps(js))

    try:
        validate_slug(request.POST['username'])
    except:
        js['value']="Username should only consist of A-Z and 0-9.".format(field=a)
        return HttpResponse(json.dumps(js))
        
    

    # Confirm username and e-mail are unique. TODO: This should be in a transaction
    if len(User.objects.filter(username=request.POST['username']))>0:
        js['value']="An account with this username already exists."
        return HttpResponse(json.dumps(js))

    if len(User.objects.filter(email=request.POST['email']))>0:
        js['value']="An account with this e-mail already exists."
        return HttpResponse(json.dumps(js))

    u=User(username=request.POST['username'],
           email=request.POST['email'],
           is_active=False)
    u.set_password(request.POST['password'])
    r=Registration()
    # TODO: Rearrange so that if part of the process fails, the whole process fails. 
    # Right now, we can have e.g. no registration e-mail sent out and a zombie account
    u.save()
    r.register(u)

    up=UserProfile(user=u)
    up.name=request.POST['name']
    up.language=request.POST['language']
    up.location=request.POST['location']
    up.save()

    d={'name':request.POST['name'],
       'key':r.activation_key,
       'site':settings.SITE_NAME}

    subject = render_to_string('activation_email_subject.txt',d)
        # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string('activation_email.txt',d)

    try:
        res=u.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    except:
        js['value']=str(sys.exc_info())
        return HttpResponse(json.dumps(js))
        
    js={'success':True,
        'value':render_to_string('registration/reg_complete.html', {'email':request.POST['email'], 
                                                                    'csrf':csrf(request)['csrf_token']})}
    return HttpResponse(json.dumps(js), mimetype="application/json")

def activate_account(request, key):
    r=Registration.objects.filter(activation_key=key)
    if len(r)==1:
        r[0].activate()
        return render_to_response("activation_complete.html",{'csrf':csrf(request)['csrf_token']})
    if len(r)==0:
        return render_to_response("activation_invalid.html",{'csrf':csrf(request)['csrf_token']})
    return HttpResponse("Unknown error. Please e-mail us to let us know how it happened.")
