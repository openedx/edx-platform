import datetime
import json
import logging
import random
import string
import sys
import uuid

from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.mail import send_mail
from django.core.validators import validate_email, validate_slug, ValidationError
from django.db import connection
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
from mako import exceptions

from django_future.csrf import ensure_csrf_cookie

from student.survey_questions import exit_survey_list_for_student
from models import Registration, UserProfile, PendingNameChange, PendingEmailChange

log = logging.getLogger("mitx.student")

def csrf_token(context):
    ''' A csrf token that can be included in a form. 
    '''
    csrf_token = context.get('csrf_token', '')
    if csrf_token == 'NOTPROVIDED':
        return ''
    return u'<div style="display:none"><input type="hidden" name="csrfmiddlewaretoken" value="%s" /></div>' % (csrf_token)

@ensure_csrf_cookie
def index(request):
    ''' Redirects to main page -- info page if user authenticated, or marketing if not
    '''
    if settings.COURSEWARE_ENABLED and request.user.is_authenticated():
        return redirect('/info')
    else:
        csrf_token = csrf(request)['csrf_token']
        # TODO: Clean up how 'error' is done. 
        return render_to_response('index.html', {'csrf': csrf_token }) 
                                                 
# Need different levels of logging
@ensure_csrf_cookie
def login_user(request, error=""):
    ''' AJAX request to log in the user. '''
    if 'email' not in request.POST or 'password' not in request.POST:
        return HttpResponse(json.dumps({'success':False, 
                                        'error': 'Invalid login'})) # TODO: User error message

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
    ''' HTTP request to log in the user. Redirects to marketing page'''
    logout(request)
    return redirect('/')

@ensure_csrf_cookie
def change_setting(request):
    ''' JSON call to change a profile setting: Right now, location and language
    '''
    if not request.user.is_authenticated():
        return redirect('/')
    up = UserProfile.objects.get(user=request.user) #request.user.profile_cache
    if 'location' in request.POST:
        up.location=request.POST['location']
    if 'language' in request.POST:
        up.language=request.POST['language']
    up.save()

    return HttpResponse(json.dumps({'success':True, 
                                    'language':up.language,
                                    'location':up.location,}))

@ensure_csrf_cookie
def create_account(request, post_override=None):
    ''' JSON call to enroll in the course. '''
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
    for a in ['username', 'email', 'name', 'password', 'terms_of_service', 'honor_code']:
        if len(post_vars[a])<2:
            error_str = {'username' : 'Username of length 2 or greater', 
                         'email' : 'Properly formatted e-mail',
                         'name' : 'Your legal name ',
                         'password': 'Valid password ',
                         'terms_of_service': 'Accepting Terms of Service',
                         'honor_code': 'Agreeing to the Honor Code'}
            js['value']="{field} is required.".format(field=error_str[a])
            return HttpResponse(json.dumps(js))

    try:
        validate_email(post_vars['email'])
    except ValidationError:
        js['value']="Valid e-mail is required.".format(field=a)
        return HttpResponse(json.dumps(js))

    try:
        validate_slug(post_vars['username'])
    except ValidationError:
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

    up = UserProfile(user=u)
    up.name=post_vars['name']
    up.language=post_vars['language']
    up.location=post_vars['location']
    up.save()

    d={'name':post_vars['name'],
       'key':r.activation_key}

    subject = render_to_string('emails/activation_email_subject.txt',d)
        # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt',d)

    try:
        if not settings.GENERATE_RANDOM_USER_CREDENTIALS:
            res=u.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    except:
        log.exception(sys.exc_info())
        js['value']='Could not send activation e-mail.'
        return HttpResponse(json.dumps(js))
        
    js={'success':True,
        'value':render_to_string('registration/reg_complete.html', {'email':post_vars['email'], 
                                                                    'csrf':csrf(request)['csrf_token']})}
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
        
        return create_account_function(request, post_override = post_override)
        
    return inner_create_random_account

if settings.GENERATE_RANDOM_USER_CREDENTIALS:
    create_account = create_random_account(create_account)

@ensure_csrf_cookie
def activate_account(request, key):
    ''' When link in activation e-mail is clicked
    '''
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

@ensure_csrf_cookie
def reactivation_email(request):
    ''' Send an e-mail to reactivate a deactivated account, or to
    resend an activation e-mail. Untested. '''
    email = request.POST['email']
    try: 
        user = User.objects.get(email = 'email')
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'success':False,
                                        'error': 'No inactive user with this e-mail exists'}))
    
    if user.is_active:
        return HttpResponse(json.dumps({'success':False,
                                        'error': 'User is already active'}))
    
    reg = Registration.objects.get(user = user)
    reg.register(user)

    d={'name':UserProfile.get(user = user).name,
       'key':r.activation_key}
    
    subject = render_to_string('reactivation_email_subject.txt',d)
    subject = ''.join(subject.splitlines())
    message = render_to_string('reactivation_email.txt',d)

    res=u.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    
    return HttpResponse(json.dumps({'success':True}))


@ensure_csrf_cookie
def change_email_request(request):
    ''' AJAX call from the profile page. User wants a new e-mail. 
    '''
    ## Make sure it checks for existing e-mail conflicts
    if not request.user.is_authenticated:
        raise Http404
    
    user = request.user

    if not user.check_password(request.POST['password']):
        return HttpResponse(json.dumps({'success':False, 
                                        'error':'Invalid password'})) 
    
    new_email = request.POST['new_email']
    try:
        validate_email(new_email)
    except ValidationError:
        return HttpResponse(json.dumps({'success':False, 
                                        'error':'Valid e-mail address required.'}))

    if len(User.objects.filter(email = new_email)) != 0:
        ## CRITICAL TODO: Handle case sensitivity for e-mails
        return HttpResponse(json.dumps({'success':False, 
                                        'error':'An account with this e-mail already exists.'}))

    pec_list = PendingEmailChange.objects.filter(user = request.user)
    if len(pec_list) == 0: 
        pec = PendingEmailChange()
        pec.user = user
    else :
        pec = pec_list[0]

    pec.new_email = request.POST['new_email']
    pec.activation_key = uuid.uuid4().hex
    pec.save()

    if pec.new_email == user.email: 
        pec.delete()
        return HttpResponse(json.dumps({'success':False, 
                                        'error':'Old email is the same as the new email.'}))        

    d = {'key':pec.activation_key, 
         'old_email' : user.email, 
         'new_email' : pec.new_email}

    subject = render_to_string('emails/email_change_subject.txt',d)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/email_change.txt',d)

    res=send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [pec.new_email])

    return HttpResponse(json.dumps({'success':True}))

@ensure_csrf_cookie
def confirm_email_change(request, key):
    ''' User requested a new e-mail. This is called when the activation 
    link is clicked. We confirm with the old e-mail, and update
    '''
    try:
        pec=PendingEmailChange.objects.get(activation_key=key)
    except PendingEmailChange.DoesNotExist:
        return render_to_response("invalid_email_key.html", {})
    
    user = pec.user
    d = {'old_email' : user.email, 
         'new_email' : pec.new_email}

    if len(User.objects.filter(email = pec.new_email)) != 0:
        return render_to_response("email_exists.html", d)


    subject = render_to_string('emails/email_change_subject.txt',d)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/confirm_email_change.txt',d)
    up = UserProfile.objects.get( user = user )
    meta = up.get_meta()
    if 'old_emails' not in meta:
        meta['old_emails'] = []
    meta['old_emails'].append([user.email, datetime.datetime.now().isoformat()])
    up.set_meta(meta)
    up.save()
    user.email = pec.new_email
    user.save()
    pec.delete()
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

    return render_to_response("email_change_successful.html", d)

@ensure_csrf_cookie
def change_name_request(request):
    ''' Log a request for a new name. '''
    if not request.user.is_authenticated:
        raise Http404
    
    try: 
        pnc = PendingNameChange.objects.get(user = request.user)
    except PendingNameChange.DoesNotExist:
        pnc = PendingNameChange()
    pnc.user = request.user
    pnc.new_name = request.POST['new_name']
    pnc.rationale = request.POST['rationale']
    if len(pnc.new_name)<2:
        return HttpResponse(json.dumps({'success':False,'error':'Name required'})) 
    if len(pnc.rationale)<2:
        return HttpResponse(json.dumps({'success':False,'error':'Rationale required'})) 
    pnc.save()
    return HttpResponse(json.dumps({'success':True})) 

@ensure_csrf_cookie
def pending_name_changes(request):
    ''' Web page which allows staff to approve or reject name changes. '''
    if not request.user.is_staff:
        raise Http404

    changes = list(PendingNameChange.objects.all())
    js = {'students' : [{'new_name': c.new_name, 
                         'rationale':c.rationale, 
                         'old_name':UserProfile.objects.get(user=c.user).name, 
                         'email':c.user.email,
                         'uid':c.user.id,
                         'cid':c.id} for c in changes]}
    return render_to_response('name_changes.html', js) 

@ensure_csrf_cookie
def reject_name_change(request):
    ''' JSON: Name change process. Course staff clicks 'reject' on a given name change '''
    if not request.user.is_staff:
        raise Http404

    try: 
        pnc = PendingNameChange.objects.get(id = int(request.POST['id']))
    except PendingNameChange.DoesNotExist: 
        return HttpResponse(json.dumps({'success':False, 'error':'Invalid ID'})) 

    pnc.delete()
    return HttpResponse(json.dumps({'success':True})) 

@ensure_csrf_cookie
def accept_name_change(request):
    ''' JSON: Name change process. Course staff clicks 'accept' on a given name change '''
    if not request.user.is_staff:
        raise Http404

    try: 
        pnc = PendingNameChange.objects.get(id = int(request.POST['id']))
    except PendingNameChange.DoesNotExist: 
        return HttpResponse(json.dumps({'success':False, 'error':'Invalid ID'})) 

    u = pnc.user
    up = UserProfile.objects.get(user=u)

    # Save old name
    meta = up.get_meta()
    if 'old_names' not in meta:
        meta['old_names'] = []
    meta['old_names'].append([up.name, pnc.rationale, datetime.datetime.now().isoformat()])
    up.set_meta(meta)

    up.name = pnc.new_name
    up.save()
    pnc.delete()

    return HttpResponse(json.dumps({'success':True})) 
    
    
    
@login_required
def record_exit_survey(request, internal_request = False):
    if not settings.END_COURSE_ENABLED:
        raise Http404 
    
    if request.method == "POST":
        # If internal_request = True, this is a survey that was submitted with another form
        # We will record it and return the results as a dictionary, instead of a json HttpResponse
        def returnResults(return_data):
            if internal_request:
                return return_data
            else:
                return HttpResponse(json.dumps(return_data))
        
        if 'survey_results' not in request.POST:
            if internal_request:
                return returnResults({'success':True})
            else:
                return returnResults({'success':False, 'error':'There was a problem receiving your survey response.'}) 
    
        response = json.loads(request.POST['survey_results'])
        
        up = UserProfile.objects.get(user=request.user)
    
        meta = up.get_meta()
        if '6002x_exit_response' in meta:
            # Once we got a response, we don't show them the survey form again, so this is a really odd case anyway
            log.warning("Received an extra survey response. " + request.POST['survey_results'])
            return returnResults({'success':True})
            
        else:
            if internal_request and all( value == None or value == [''] for value in response.values() ):
                # If all values are empty, then the student didn't answer any questions.
                # In the case of this being an internal request, we don't mark the survey as taken
                return returnResults({'success':True})
            
            meta['6002x_exit_response'] = response
            up.set_meta(meta)
            up.save()
            return returnResults({'success':True})
    
    else:
        user_info = UserProfile.objects.get(user=request.user)
        
        took_survey = student_took_survey(user_info)
        if settings.DEBUG_SURVEY:
            took_survey = False
        survey_list = []
        if not took_survey:
            survey_list = exit_survey_list_for_student(request.user)
        
        
        context = {'took_survey' : took_survey,
                 'survey_list' : survey_list}
        
        return render_to_response('exit_survey.html', context)
    
def student_took_survey(userprofile):
    meta = userprofile.get_meta()
    
    return '6002x_exit_response' in meta
