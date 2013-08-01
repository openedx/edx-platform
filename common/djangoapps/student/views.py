import datetime
import feedparser
import json
import logging
import random
import re
import string       # pylint: disable=W0402
import urllib
import uuid
import time

from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_reset_confirm
from django.core.cache import cache
from django.core.context_processors import csrf
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import validate_email, validate_slug, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed, Http404
from django.shortcuts import redirect
from django_future.csrf import ensure_csrf_cookie
from django.utils.http import cookie_date
from django.utils.http import base36_to_int
from django.utils.translation import ugettext as _

from mitxmako.shortcuts import render_to_response, render_to_string
from bs4 import BeautifulSoup

from student.models import (Registration, UserProfile, TestCenterUser, TestCenterUserForm,
                            TestCenterRegistration, TestCenterRegistrationForm,
                            PendingNameChange, PendingEmailChange,
                            CourseEnrollment, unique_id_for_user,
                            get_testcenter_registration, CourseEnrollmentAllowed)

from student.forms import PasswordResetFormNoActive

from certificates.models import CertificateStatuses, certificate_status_for_student

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.django import modulestore

from collections import namedtuple

from courseware.courses import get_courses, sort_by_announcement
from courseware.access import has_access

from external_auth.models import ExternalAuthMap

from statsd import statsd
from pytz import UTC

log = logging.getLogger("mitx.student")
Article = namedtuple('Article', 'title url author image deck publication publish_date')


def csrf_token(context):
    ''' A csrf token that can be included in a form.
    '''
    csrf_token = context.get('csrf_token', '')
    if csrf_token == 'NOTPROVIDED':
        return ''
    return (u'<div style="display:none"><input type="hidden"'
            ' name="csrfmiddlewaretoken" value="%s" /></div>' % (csrf_token))


# NOTE: This view is not linked to directly--it is called from
# branding/views.py:index(), which is cached for anonymous users.
# This means that it should always return the same thing for anon
# users. (in particular, no switching based on query params allowed)
def index(request, extra_context={}, user=None):
    '''
    Render the edX main page.

    extra_context is used to allow immediate display of certain modal windows, eg signup,
    as used by external_auth.
    '''

    # The course selection work is done in courseware.courses.
    domain = settings.MITX_FEATURES.get('FORCE_UNIVERSITY_DOMAIN')  # normally False
    # do explicit check, because domain=None is valid
    if domain == False:
        domain = request.META.get('HTTP_HOST')

    courses = get_courses(None, domain=domain)
    courses = sort_by_announcement(courses)

    context = {'courses': courses}
    context.update(extra_context)
    return render_to_response('index.html', context)


def course_from_id(course_id):
    """Return the CourseDescriptor corresponding to this course_id"""
    course_loc = CourseDescriptor.id_to_location(course_id)
    return modulestore().get_instance(course_id, course_loc)

day_pattern = re.compile(r'\s\d+,\s')
multimonth_pattern = re.compile(r'\s?\-\s?\S+\s')


def get_date_for_press(publish_date):
    import datetime
    # strip off extra months, and just use the first:
    date = re.sub(multimonth_pattern, ", ", publish_date)
    if re.search(day_pattern, date):
        date = datetime.datetime.strptime(date, "%B %d, %Y").replace(tzinfo=UTC)
    else:
        date = datetime.datetime.strptime(date, "%B, %Y").replace(tzinfo=UTC)
    return date


def press(request):
    json_articles = cache.get("student_press_json_articles")
    if json_articles is None:
        if hasattr(settings, 'RSS_URL'):
            content = urllib.urlopen(settings.PRESS_URL).read()
            json_articles = json.loads(content)
        else:
            content = open(settings.PROJECT_ROOT / "templates" / "press.json").read()
            json_articles = json.loads(content)
        cache.set("student_press_json_articles", json_articles)
    articles = [Article(**article) for article in json_articles]
    articles.sort(key=lambda item: get_date_for_press(item.publish_date), reverse=True)
    return render_to_response('static_templates/press.html', {'articles': articles})


def process_survey_link(survey_link, user):
    """
    If {UNIQUE_ID} appears in the link, replace it with a unique id for the user.
    Currently, this is sha1(user.username).  Otherwise, return survey_link.
    """
    return survey_link.format(UNIQUE_ID=unique_id_for_user(user))


def cert_info(user, course):
    """
    Get the certificate info needed to render the dashboard section for the given
    student and course.  Returns a dictionary with keys:

    'status': one of 'generating', 'ready', 'notpassing', 'processing', 'restricted'
    'show_download_url': bool
    'download_url': url, only present if show_download_url is True
    'show_disabled_download_button': bool -- true if state is 'generating'
    'show_survey_button': bool
    'survey_url': url, only if show_survey_button is True
    'grade': if status is not 'processing'
    """
    if not course.has_ended():
        return {}

    return _cert_info(user, course, certificate_status_for_student(user, course.id))


def _cert_info(user, course, cert_status):
    """
    Implements the logic for cert_info -- split out for testing.
    """
    default_status = 'processing'

    default_info = {'status': default_status,
                    'show_disabled_download_button': False,
                    'show_download_url': False,
                    'show_survey_button': False}

    if cert_status is None:
        return default_info

    # simplify the status for the template using this lookup table
    template_state = {
        CertificateStatuses.generating: 'generating',
        CertificateStatuses.regenerating: 'generating',
        CertificateStatuses.downloadable: 'ready',
        CertificateStatuses.notpassing: 'notpassing',
        CertificateStatuses.restricted: 'restricted',
    }

    status = template_state.get(cert_status['status'], default_status)

    d = {'status': status,
         'show_download_url': status == 'ready',
         'show_disabled_download_button': status == 'generating', }

    if (status in ('generating', 'ready', 'notpassing', 'restricted') and
            course.end_of_course_survey_url is not None):
        d.update({
            'show_survey_button': True,
            'survey_url': process_survey_link(course.end_of_course_survey_url, user)})
    else:
        d['show_survey_button'] = False

    if status == 'ready':
        if 'download_url' not in cert_status:
            log.warning("User %s has a downloadable cert for %s, but no download url",
                        user.username, course.id)
            return default_info
        else:
            d['download_url'] = cert_status['download_url']

    if status in ('generating', 'ready', 'notpassing', 'restricted'):
        if 'grade' not in cert_status:
            # Note: as of 11/20/2012, we know there are students in this state-- cs169.1x,
            # who need to be regraded (we weren't tracking 'notpassing' at first).
            # We can add a log.warning here once we think it shouldn't happen.
            return default_info
        else:
            d['grade'] = cert_status['grade']

    return d


@ensure_csrf_cookie
def signin_user(request):
    """
    This view will display the non-modal login form
    """
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    context = {
        'course_id': request.GET.get('course_id'),
        'enrollment_action': request.GET.get('enrollment_action')
    }
    return render_to_response('login.html', context)


@ensure_csrf_cookie
def register_user(request, extra_context={}):
    """
    This view will display the non-modal registration form
    """
    if request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    context = {
        'course_id': request.GET.get('course_id'),
        'enrollment_action': request.GET.get('enrollment_action')
    }
    context.update(extra_context)

    return render_to_response('register.html', context)


@login_required
@ensure_csrf_cookie
def dashboard(request):
    user = request.user
    enrollments = CourseEnrollment.objects.filter(user=user)

    # Build our courses list for the user, but ignore any courses that no longer
    # exist (because the course IDs have changed). Still, we don't delete those
    # enrollments, because it could have been a data push snafu.
    courses = []
    for enrollment in enrollments:
        try:
            courses.append(course_from_id(enrollment.course_id))
        except ItemNotFoundError:
            log.error("User {0} enrolled in non-existent course {1}"
                      .format(user.username, enrollment.course_id))

    message = ""
    if not user.is_active:
        message = render_to_string('registration/activate_account_notice.html', {'email': user.email})

    # Global staff can see what courses errored on their dashboard
    staff_access = False
    errored_courses = {}
    if has_access(user, 'global', 'staff'):
        # Show any courses that errored on load
        staff_access = True
        errored_courses = modulestore().get_errored_courses()

    show_courseware_links_for = frozenset(course.id for course in courses
                                          if has_access(request.user, course, 'load'))

    cert_statuses = {course.id: cert_info(request.user, course) for course in courses}

    exam_registrations = {course.id: exam_registration_info(request.user, course) for course in courses}

    # get info w.r.t ExternalAuthMap
    external_auth_map = None
    try:
        external_auth_map = ExternalAuthMap.objects.get(user=user)
    except ExternalAuthMap.DoesNotExist:
        pass

    context = {'courses': courses,
               'message': message,
               'external_auth_map': external_auth_map,
               'staff_access': staff_access,
               'errored_courses': errored_courses,
               'show_courseware_links_for': show_courseware_links_for,
               'cert_statuses': cert_statuses,
               'exam_registrations': exam_registrations,
               }

    return render_to_response('dashboard.html', context)


def try_change_enrollment(request):
    """
    This method calls change_enrollment if the necessary POST
    parameters are present, but does not return anything. It
    simply logs the result or exception. This is usually
    called after a registration or login, as secondary action.
    It should not interrupt a successful registration or login.
    """
    if 'enrollment_action' in request.POST:
        try:
            enrollment_response = change_enrollment(request)
            # There isn't really a way to display the results to the user, so we just log it
            # We expect the enrollment to be a success, and will show up on the dashboard anyway
            log.info(
                "Attempted to automatically enroll after login. Response code: {0}; response body: {1}".format(
                    enrollment_response.status_code,
                    enrollment_response.content
                )
            )
        except Exception, e:
            log.exception("Exception automatically enrolling after login: {0}".format(str(e)))


def change_enrollment(request):
    """
    Modify the enrollment status for the logged-in user.

    The request parameter must be a POST request (other methods return 405)
    that specifies course_id and enrollment_action parameters. If course_id or
    enrollment_action is not specified, if course_id is not valid, if
    enrollment_action is something other than "enroll" or "unenroll", if
    enrollment_action is "enroll" and enrollment is closed for the course, or
    if enrollment_action is "unenroll" and the user is not enrolled in the
    course, a 400 error will be returned. If the user is not logged in, 403
    will be returned; it is important that only this case return 403 so the
    front end can redirect the user to a registration or login page when this
    happens. This function should only be called from an AJAX request or
    as a post-login/registration helper, so the error messages in the responses
    should never actually be user-visible.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    user = request.user
    if not user.is_authenticated():
        return HttpResponseForbidden()

    action = request.POST.get("enrollment_action")
    course_id = request.POST.get("course_id")
    if course_id is None:
        return HttpResponseBadRequest(_("Course id not specified"))

    if action == "enroll":
        # Make sure the course exists
        # We don't do this check on unenroll, or a bad course id can't be unenrolled from
        try:
            course = course_from_id(course_id)
        except ItemNotFoundError:
            log.warning("User {0} tried to enroll in non-existent course {1}"
                        .format(user.username, course_id))
            return HttpResponseBadRequest(_("Course id is invalid"))

        if not has_access(user, course, 'enroll'):
            return HttpResponseBadRequest(_("Enrollment is closed"))

        org, course_num, run = course_id.split("/")
        statsd.increment("common.student.enrollment",
                         tags=["org:{0}".format(org),
                               "course:{0}".format(course_num),
                               "run:{0}".format(run)])

        try:
            enrollment, created = CourseEnrollment.objects.get_or_create(user=user, course_id=course.id)
        except IntegrityError:
            # If we've already created this enrollment in a separate transaction,
            # then just continue
            pass
        return HttpResponse()

    elif action == "unenroll":
        try:
            enrollment = CourseEnrollment.objects.get(user=user, course_id=course_id)
            enrollment.delete()

            org, course_num, run = course_id.split("/")
            statsd.increment("common.student.unenrollment",
                             tags=["org:{0}".format(org),
                                   "course:{0}".format(course_num),
                                   "run:{0}".format(run)])

            return HttpResponse()
        except CourseEnrollment.DoesNotExist:
            return HttpResponseBadRequest(_("You are not enrolled in this course"))
    else:
        return HttpResponseBadRequest(_("Enrollment action is invalid"))


@ensure_csrf_cookie
def accounts_login(request, error=""):

    return render_to_response('login.html', {'error': error})


# Need different levels of logging
@ensure_csrf_cookie
def login_user(request, error=""):
    ''' AJAX request to log in the user. '''
    if 'email' not in request.POST or 'password' not in request.POST:
        return HttpResponse(json.dumps({'success': False,
                                        'value': _('There was an error receiving your login information. Please email us.')}))  # TODO: User error message

    email = request.POST['email']
    password = request.POST['password']
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        log.warning(u"Login failed - Unknown user email: {0}".format(email))
        return HttpResponse(json.dumps({'success': False,
                                        'value': _('Email or password is incorrect.')}))  # TODO: User error message

    username = user.username
    user = authenticate(username=username, password=password)
    if user is None:
        log.warning(u"Login failed - password for {0} is invalid".format(email))
        return HttpResponse(json.dumps({'success': False,
                                        'value': _('Email or password is incorrect.')}))

    if user is not None and user.is_active:
        try:
            login(request, user)
            if request.POST.get('remember') == 'true':
                request.session.set_expiry(604800)
                log.debug("Setting user session to never expire")
            else:
                request.session.set_expiry(0)
        except Exception as e:
            log.critical("Login failed - Could not create session. Is memcached running?")
            log.exception(e)

        log.info(u"Login success - {0} ({1})".format(username, email))

        try_change_enrollment(request)

        statsd.increment(_("common.student.successful_login"))
        response = HttpResponse(json.dumps({'success': True}))

        # set the login cookie for the edx marketing site
        # we want this cookie to be accessed via javascript
        # so httponly is set to None

        if request.session.get_expire_at_browser_close():
            max_age = None
            expires = None
        else:
            max_age = request.session.get_expiry_age()
            expires_time = time.time() + max_age
            expires = cookie_date(expires_time)

        response.set_cookie(settings.EDXMKTG_COOKIE_NAME,
                            'true', max_age=max_age,
                            expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                            path='/',
                            secure=None,
                            httponly=None)

        return response

    log.warning(u"Login failed - Account not active for user {0}, resending activation".format(username))

    reactivation_email_for_user(user)
    not_activated_msg = _("This account has not been activated. We have sent another activation message. Please check your e-mail for the activation instructions.")
    return HttpResponse(json.dumps({'success': False,
                                    'value': not_activated_msg}))


@ensure_csrf_cookie
def logout_user(request):
    '''
    HTTP request to log out the user. Redirects to marketing page.
    Deletes both the CSRF and sessionid cookies so the marketing
    site can determine the logged in state of the user
    '''

    logout(request)
    response = redirect('/')
    response.delete_cookie(settings.EDXMKTG_COOKIE_NAME,
                           path='/',
                           domain=settings.SESSION_COOKIE_DOMAIN)
    return response


@login_required
@ensure_csrf_cookie
def change_setting(request):
    ''' JSON call to change a profile setting: Right now, location
    '''
    # TODO (vshnayder): location is no longer used
    up = UserProfile.objects.get(user=request.user)  # request.user.profile_cache
    if 'location' in request.POST:
        up.location = request.POST['location']
    up.save()

    return HttpResponse(json.dumps({'success': True,
                                    'location': up.location, }))


def _do_create_account(post_vars):
    """
    Given cleaned post variables, create the User and UserProfile objects, as well as the
    registration for this user.

    Returns a tuple (User, UserProfile, Registration).

    Note: this function is also used for creating test users.
    """
    user = User(username=post_vars['username'],
                email=post_vars['email'],
                is_active=False)
    user.set_password(post_vars['password'])
    registration = Registration()
    # TODO: Rearrange so that if part of the process fails, the whole process fails.
    # Right now, we can have e.g. no registration e-mail sent out and a zombie account
    try:
        user.save()
    except IntegrityError:
        js = {'success': False}
        # Figure out the cause of the integrity error
        if len(User.objects.filter(username=post_vars['username'])) > 0:
            js['value'] = _("An account with the Public Username '{username}' already exists.").format(username=post_vars['username'])
            js['field'] = 'username'
            return HttpResponse(json.dumps(js))

        if len(User.objects.filter(email=post_vars['email'])) > 0:
            js['value'] = _("An account with the Email '{email}' already exists.").format(email=post_vars['email'])
            js['field'] = 'email'
            return HttpResponse(json.dumps(js))

        raise

    registration.register(user)

    profile = UserProfile(user=user)
    profile.name = post_vars['name']
    profile.level_of_education = post_vars.get('level_of_education')
    profile.gender = post_vars.get('gender')
    profile.mailing_address = post_vars.get('mailing_address')
    profile.goals = post_vars.get('goals')

    try:
        profile.year_of_birth = int(post_vars['year_of_birth'])
    except (ValueError, KeyError):
        # If they give us garbage, just ignore it instead
        # of asking them to put an integer.
        profile.year_of_birth = None
    try:
        profile.save()
    except Exception:
        log.exception("UserProfile creation failed for user {id}.".format(id=user.id))
    return (user, profile, registration)


@ensure_csrf_cookie
def create_account(request, post_override=None):
    '''
    JSON call to create new edX account.
    Used by form in signup_modal.html, which is included into navigation.html
    '''
    js = {'success': False}

    post_vars = post_override if post_override else request.POST

    # if doing signup for an external authorization, then get email, password, name from the eamap
    # don't use the ones from the form, since the user could have hacked those
    # unless originally we didn't get a valid email or name from the external auth
    DoExternalAuth = 'ExternalAuthMap' in request.session
    if DoExternalAuth:
        eamap = request.session['ExternalAuthMap']
        try:
            validate_email(eamap.external_email)
            email = eamap.external_email
        except ValidationError:
            email = post_vars.get('email', '')
        if eamap.external_name.strip() == '':
            name = post_vars.get('name', '')
        else:
            name = eamap.external_name
        password = eamap.internal_password
        post_vars = dict(post_vars.items())
        post_vars.update(dict(email=email, name=name, password=password))
        log.info('In create_account with external_auth: post_vars = %s' % post_vars)

    # Confirm we have a properly formed request
    for a in ['username', 'email', 'password', 'name']:
        if a not in post_vars:
            js['value'] = _("Error (401 {field}). E-mail us.").format(field=a)
            js['field'] = a
            return HttpResponse(json.dumps(js))

    if post_vars.get('honor_code', 'false') != u'true':
        js['value'] = _("To enroll, you must follow the honor code.").format(field=a)
        js['field'] = 'honor_code'
        return HttpResponse(json.dumps(js))

    # Can't have terms of service for certain SHIB users, like at Stanford
    tos_not_required = settings.MITX_FEATURES.get("AUTH_USE_SHIB") \
                       and settings.MITX_FEATURES.get('SHIB_DISABLE_TOS') \
                       and DoExternalAuth and ("shib" in eamap.external_domain)

    if not tos_not_required:
        if post_vars.get('terms_of_service', 'false') != u'true':
            js['value'] = _("You must accept the terms of service.").format(field=a)
            js['field'] = 'terms_of_service'
            return HttpResponse(json.dumps(js))

    # Confirm appropriate fields are there.
    # TODO: Check e-mail format is correct.
    # TODO: Confirm e-mail is not from a generic domain (mailinator, etc.)? Not sure if
    # this is a good idea
    # TODO: Check password is sane

    required_post_vars = ['username', 'email', 'name', 'password', 'terms_of_service', 'honor_code']
    if tos_not_required:
        required_post_vars =  ['username', 'email', 'name', 'password', 'honor_code']

    for a in required_post_vars:
        if len(post_vars[a]) < 2:
            error_str = {'username': 'Username must be minimum of two characters long.',
                         'email': 'A properly formatted e-mail is required.',
                         'name': 'Your legal name must be a minimum of two characters long.',
                         'password': 'A valid password is required.',
                         'terms_of_service': 'Accepting Terms of Service is required.',
                         'honor_code': 'Agreeing to the Honor Code is required.'}
            js['value'] = error_str[a]
            js['field'] = a
            return HttpResponse(json.dumps(js))

    try:
        validate_email(post_vars['email'])
    except ValidationError:
        js['value'] = _("Valid e-mail is required.").format(field=a)
        js['field'] = 'email'
        return HttpResponse(json.dumps(js))

    try:
        validate_slug(post_vars['username'])
    except ValidationError:
        js['value'] = _("Username should only consist of A-Z and 0-9, with no spaces.").format(field=a)
        js['field'] = 'username'
        return HttpResponse(json.dumps(js))

    # Ok, looks like everything is legit.  Create the account.
    ret = _do_create_account(post_vars)
    if isinstance(ret, HttpResponse):  # if there was an error then return that
        return ret
    (user, profile, registration) = ret

    d = {'name': post_vars['name'],
         'key': registration.activation_key,
         }

    # composes activation email
    subject = render_to_string('emails/activation_email_subject.txt', d)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt', d)

    # dont send email if we are doing load testing or random user generation for some reason
    if not (settings.MITX_FEATURES.get('AUTOMATIC_AUTH_FOR_LOAD_TESTING')):
        try:
            if settings.MITX_FEATURES.get('REROUTE_ACTIVATION_EMAIL'):
                dest_addr = settings.MITX_FEATURES['REROUTE_ACTIVATION_EMAIL']
                message = ("Activation for %s (%s): %s\n" % (user, user.email, profile.name) +
                           '-' * 80 + '\n\n' + message)
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [dest_addr], fail_silently=False)
            else:
                res = user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        except:
            log.warning('Unable to send activation email to user', exc_info=True)
            js['value'] = _('Could not send activation e-mail.')
            return HttpResponse(json.dumps(js))

    # Immediately after a user creates an account, we log them in. They are only
    # logged in until they close the browser. They can't log in again until they click
    # the activation link from the email.
    login_user = authenticate(username=post_vars['username'], password=post_vars['password'])
    login(request, login_user)
    request.session.set_expiry(0)

    if DoExternalAuth:
        eamap.user = login_user
        eamap.dtsignup = datetime.datetime.now(UTC)
        eamap.save()
        log.info("User registered with external_auth %s" % post_vars['username'])
        log.info('Updated ExternalAuthMap for %s to be %s' % (post_vars['username'], eamap))

        if settings.MITX_FEATURES.get('BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'):
            log.info('bypassing activation email')
            login_user.is_active = True
            login_user.save()

    try_change_enrollment(request)

    statsd.increment("common.student.account_created")

    js = {'success': True}
    HttpResponse(json.dumps(js), mimetype="application/json")

    response = HttpResponse(json.dumps({'success': True}))

    # set the login cookie for the edx marketing site
    # we want this cookie to be accessed via javascript
    # so httponly is set to None

    if request.session.get_expire_at_browser_close():
        max_age = None
        expires = None
    else:
        max_age = request.session.get_expiry_age()
        expires_time = time.time() + max_age
        expires = cookie_date(expires_time)

    response.set_cookie(settings.EDXMKTG_COOKIE_NAME,
                        'true', max_age=max_age,
                        expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        path='/',
                        secure=None,
                        httponly=None)
    return response


def exam_registration_info(user, course):
    """ Returns a Registration object if the user is currently registered for a current
    exam of the course.  Returns None if the user is not registered, or if there is no
    current exam for the course.
    """
    exam_info = course.current_test_center_exam
    if exam_info is None:
        return None

    exam_code = exam_info.exam_series_code
    registrations = get_testcenter_registration(user, course.id, exam_code)
    if registrations:
        registration = registrations[0]
    else:
        registration = None
    return registration


@login_required
@ensure_csrf_cookie
def begin_exam_registration(request, course_id):
    """ Handles request to register the user for the current
    test center exam of the specified course.  Called by form
    in dashboard.html.
    """
    user = request.user

    try:
        course = course_from_id(course_id)
    except ItemNotFoundError:
        log.error("User {0} enrolled in non-existent course {1}".format(user.username, course_id))
        raise Http404

    # get the exam to be registered for:
    # (For now, we just assume there is one at most.)
    # if there is no exam now (because someone bookmarked this stupid page),
    # then return a 404:
    exam_info = course.current_test_center_exam
    if exam_info is None:
        raise Http404

    # determine if the user is registered for this course:
    registration = exam_registration_info(user, course)

    # we want to populate the registration page with the relevant information,
    # if it already exists.  Create an empty object otherwise.
    try:
        testcenteruser = TestCenterUser.objects.get(user=user)
    except TestCenterUser.DoesNotExist:
        testcenteruser = TestCenterUser()
        testcenteruser.user = user

    context = {'course': course,
               'user': user,
               'testcenteruser': testcenteruser,
               'registration': registration,
               'exam_info': exam_info,
               }

    return render_to_response('test_center_register.html', context)


@ensure_csrf_cookie
def create_exam_registration(request, post_override=None):
    '''
    JSON call to create a test center exam registration.
    Called by form in test_center_register.html
    '''
    post_vars = post_override if post_override else request.POST

    # first determine if we need to create a new TestCenterUser, or if we are making any update
    # to an existing TestCenterUser.
    username = post_vars['username']
    user = User.objects.get(username=username)
    course_id = post_vars['course_id']
    course = course_from_id(course_id)  # assume it will be found....

    # make sure that any demographic data values received from the page have been stripped.
    # Whitespace is not an acceptable response for any of these values
    demographic_data = {}
    for fieldname in TestCenterUser.user_provided_fields():
        if fieldname in post_vars:
            demographic_data[fieldname] = (post_vars[fieldname]).strip()
    try:
        testcenter_user = TestCenterUser.objects.get(user=user)
        needs_updating = testcenter_user.needs_update(demographic_data)
        log.info("User {0} enrolled in course {1} {2}updating demographic info for exam registration".format(user.username, course_id, "" if needs_updating else "not "))
    except TestCenterUser.DoesNotExist:
        # do additional initialization here:
        testcenter_user = TestCenterUser.create(user)
        needs_updating = True
        log.info("User {0} enrolled in course {1} creating demographic info for exam registration".format(user.username, course_id))

    # perform validation:
    if needs_updating:
        # first perform validation on the user information
        # using a Django Form.
        form = TestCenterUserForm(instance=testcenter_user, data=demographic_data)
        if form.is_valid():
            form.update_and_save()
        else:
            response_data = {'success': False}
            # return a list of errors...
            response_data['field_errors'] = form.errors
            response_data['non_field_errors'] = form.non_field_errors()
            return HttpResponse(json.dumps(response_data), mimetype="application/json")

    # create and save the registration:
    needs_saving = False
    exam = course.current_test_center_exam
    exam_code = exam.exam_series_code
    registrations = get_testcenter_registration(user, course_id, exam_code)
    if registrations:
        registration = registrations[0]
        # NOTE: we do not bother to check here to see if the registration has changed,
        # because at the moment there is no way for a user to change anything about their
        # registration.  They only provide an optional accommodation request once, and
        # cannot make changes to it thereafter.
        # It is possible that the exam_info content has been changed, such as the
        # scheduled exam dates, but those kinds of changes should not be handled through
        # this registration screen.

    else:
        accommodation_request = post_vars.get('accommodation_request', '')
        registration = TestCenterRegistration.create(testcenter_user, exam, accommodation_request)
        needs_saving = True
        log.info("User {0} enrolled in course {1} creating new exam registration".format(user.username, course_id))

    if needs_saving:
        # do validation of registration.  (Mainly whether an accommodation request is too long.)
        form = TestCenterRegistrationForm(instance=registration, data=post_vars)
        if form.is_valid():
            form.update_and_save()
        else:
            response_data = {'success': False}
            # return a list of errors...
            response_data['field_errors'] = form.errors
            response_data['non_field_errors'] = form.non_field_errors()
            return HttpResponse(json.dumps(response_data), mimetype="application/json")

    # only do the following if there is accommodation text to send,
    # and a destination to which to send it.
    # TODO: still need to create the accommodation email templates
#    if 'accommodation_request' in post_vars and 'TESTCENTER_ACCOMMODATION_REQUEST_EMAIL' in settings:
#        d = {'accommodation_request': post_vars['accommodation_request'] }
#
#        # composes accommodation email
#        subject = render_to_string('emails/accommodation_email_subject.txt', d)
#        # Email subject *must not* contain newlines
#        subject = ''.join(subject.splitlines())
#        message = render_to_string('emails/accommodation_email.txt', d)
#
#        try:
#            dest_addr = settings['TESTCENTER_ACCOMMODATION_REQUEST_EMAIL']
#            from_addr = user.email
#            send_mail(subject, message, from_addr, [dest_addr], fail_silently=False)
#        except:
#            log.exception(sys.exc_info())
#            response_data = {'success': False}
#            response_data['non_field_errors'] =  [ 'Could not send accommodation e-mail.', ]
#            return HttpResponse(json.dumps(response_data), mimetype="application/json")

    js = {'success': True}
    return HttpResponse(json.dumps(js), mimetype="application/json")


def auto_auth(request):
    """
    Automatically logs the user in with a generated random credentials
    This view is only accessible when
    settings.MITX_SETTINGS['AUTOMATIC_AUTH_FOR_LOAD_TESTING'] is true.
    """

    def get_dummy_post_data(username, password):
        """
        Return a dictionary suitable for passing to post_vars of _do_create_account or post_override
        of create_account, with specified username and password.
        """

        return {'username': username,
                'email': username + "_dummy_test@mitx.mit.edu",
                'password': password,
                'name': username + " " + username,
                'honor_code': u'true',
                'terms_of_service': u'true', }

    # generate random user ceredentials from a small name space (determined by settings)
    name_base = 'USER_'
    pass_base = 'PASS_'

    max_users = settings.MITX_FEATURES.get('MAX_AUTO_AUTH_USERS', 200)
    number = random.randint(1, max_users)

    username = name_base + str(number)
    password = pass_base + str(number)

    # if they already are a user, log in
    try:
        user = User.objects.get(username=username)
        user = authenticate(username=username, password=password)
        login(request, user)

    # else create and activate account info
    except ObjectDoesNotExist:
        post_override = get_dummy_post_data(username, password)
        create_account(request, post_override=post_override)
        request.user.is_active = True
        request.user.save()

    # return empty success
    return HttpResponse('')


@ensure_csrf_cookie
def activate_account(request, key):
    ''' When link in activation e-mail is clicked
    '''
    r = Registration.objects.filter(activation_key=key)
    if len(r) == 1:
        user_logged_in = request.user.is_authenticated()
        already_active = True
        if not r[0].user.is_active:
            r[0].activate()
            already_active = False

        #Enroll student in any pending courses he/she may have if auto_enroll flag is set
        student = User.objects.filter(id=r[0].user_id)
        if student:
            ceas = CourseEnrollmentAllowed.objects.filter(email=student[0].email)
            for cea in ceas:
                if cea.auto_enroll:
                    course_id = cea.course_id
                    enrollment, created = CourseEnrollment.objects.get_or_create(user_id=student[0].id, course_id=course_id)

        resp = render_to_response("registration/activation_complete.html", {'user_logged_in': user_logged_in, 'already_active': already_active})
        return resp
    if len(r) == 0:
        return render_to_response("registration/activation_invalid.html", {'csrf': csrf(request)['csrf_token']})
    return HttpResponse(_("Unknown error. Please e-mail us to let us know how it happened."))


@ensure_csrf_cookie
def password_reset(request):
    ''' Attempts to send a password reset e-mail. '''
    if request.method != "POST":
        raise Http404

    form = PasswordResetFormNoActive(request.POST)
    if form.is_valid():
        form.save(use_https=request.is_secure(),
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  request=request,
                  domain_override=request.get_host())
        return HttpResponse(json.dumps({'success': True,
                                        'value': render_to_string('registration/password_reset_done.html', {})}))
    else:
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Invalid e-mail or user')}))


def password_reset_confirm_wrapper(request, uidb36=None, token=None):
    ''' A wrapper around django.contrib.auth.views.password_reset_confirm.
        Needed because we want to set the user as active at this step.
    '''
    #cribbed from django.contrib.auth.views.password_reset_confirm
    try:
        uid_int = base36_to_int(uidb36)
        user = User.objects.get(id=uid_int)
        user.is_active = True
        user.save()
    except (ValueError, User.DoesNotExist):
        pass
    return password_reset_confirm(request, uidb36=uidb36, token=token)


def reactivation_email_for_user(user):
    try:
        reg = Registration.objects.get(user=user)
    except Registration.DoesNotExist:
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('No inactive user with this e-mail exists')}))

    d = {'name': user.profile.name,
         'key': reg.activation_key}

    subject = render_to_string('emails/activation_email_subject.txt', d)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/activation_email.txt', d)

    try:
        res = user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
    except:
        log.warning('Unable to send reactivation email', exc_info=True)
        return HttpResponse(json.dumps({'success': False, 'error': _('Unable to send reactivation email')}))

    return HttpResponse(json.dumps({'success': True}))


@ensure_csrf_cookie
def change_email_request(request):
    ''' AJAX call from the profile page. User wants a new e-mail.
    '''
    ## Make sure it checks for existing e-mail conflicts
    if not request.user.is_authenticated:
        raise Http404

    user = request.user

    if not user.check_password(request.POST['password']):
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Invalid password')}))

    new_email = request.POST['new_email']
    try:
        validate_email(new_email)
    except ValidationError:
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Valid e-mail address required.')}))

    if User.objects.filter(email=new_email).count() != 0:
        ## CRITICAL TODO: Handle case sensitivity for e-mails
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('An account with this e-mail already exists.')}))

    pec_list = PendingEmailChange.objects.filter(user=request.user)
    if len(pec_list) == 0:
        pec = PendingEmailChange()
        pec.user = user
    else:
        pec = pec_list[0]

    pec.new_email = request.POST['new_email']
    pec.activation_key = uuid.uuid4().hex
    pec.save()

    if pec.new_email == user.email:
        pec.delete()
        return HttpResponse(json.dumps({'success': False,
                                        'error': _('Old email is the same as the new email.')}))

    d = {'key': pec.activation_key,
         'old_email': user.email,
         'new_email': pec.new_email}

    subject = render_to_string('emails/email_change_subject.txt', d)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/email_change.txt', d)

    res = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [pec.new_email])

    return HttpResponse(json.dumps({'success': True}))


@ensure_csrf_cookie
@transaction.commit_manually
def confirm_email_change(request, key):
    ''' User requested a new e-mail. This is called when the activation
    link is clicked. We confirm with the old e-mail, and update
    '''
    try:
        try:
            pec = PendingEmailChange.objects.get(activation_key=key)
        except PendingEmailChange.DoesNotExist:
            transaction.rollback()
            return render_to_response("invalid_email_key.html", {})

        user = pec.user
        address_context = {
            'old_email': user.email,
            'new_email': pec.new_email
        }

        if len(User.objects.filter(email=pec.new_email)) != 0:
            transaction.rollback()
            return render_to_response("email_exists.html", {})

        subject = render_to_string('emails/email_change_subject.txt', address_context)
        subject = ''.join(subject.splitlines())
        message = render_to_string('emails/confirm_email_change.txt', address_context)
        up = UserProfile.objects.get(user=user)
        meta = up.get_meta()
        if 'old_emails' not in meta:
            meta['old_emails'] = []
        meta['old_emails'].append([user.email, datetime.datetime.now(UTC).isoformat()])
        up.set_meta(meta)
        up.save()
        # Send it to the old email...
        try:
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        except Exception:
            transaction.rollback()
            log.warning('Unable to send confirmation email to old address', exc_info=True)
            return render_to_response("email_change_failed.html", {'email': user.email})

        user.email = pec.new_email
        user.save()
        pec.delete()
        # And send it to the new email...
        try:
            user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
        except Exception:
            transaction.rollback()
            log.warning('Unable to send confirmation email to new address', exc_info=True)
            return render_to_response("email_change_failed.html", {'email': pec.new_email})

        transaction.commit()
        return render_to_response("email_change_successful.html", address_context)
    except Exception:
        # If we get an unexpected exception, be sure to rollback the transaction
        transaction.rollback()
        raise


@ensure_csrf_cookie
def change_name_request(request):
    ''' Log a request for a new name. '''
    if not request.user.is_authenticated:
        raise Http404

    try:
        pnc = PendingNameChange.objects.get(user=request.user)
    except PendingNameChange.DoesNotExist:
        pnc = PendingNameChange()
    pnc.user = request.user
    pnc.new_name = request.POST['new_name']
    pnc.rationale = request.POST['rationale']
    if len(pnc.new_name) < 2:
        return HttpResponse(json.dumps({'success': False, 'error': _('Name required')}))
    pnc.save()

    # The following automatically accepts name change requests. Remove this to
    # go back to the old system where it gets queued up for admin approval.
    accept_name_change_by_id(pnc.id)

    return HttpResponse(json.dumps({'success': True}))


@ensure_csrf_cookie
def pending_name_changes(request):
    ''' Web page which allows staff to approve or reject name changes. '''
    if not request.user.is_staff:
        raise Http404

    changes = list(PendingNameChange.objects.all())
    js = {'students': [{'new_name': c.new_name,
                        'rationale': c.rationale,
                        'old_name': UserProfile.objects.get(user=c.user).name,
                        'email': c.user.email,
                        'uid': c.user.id,
                        'cid': c.id} for c in changes]}
    return render_to_response('name_changes.html', js)


@ensure_csrf_cookie
def reject_name_change(request):
    ''' JSON: Name change process. Course staff clicks 'reject' on a given name change '''
    if not request.user.is_staff:
        raise Http404

    try:
        pnc = PendingNameChange.objects.get(id=int(request.POST['id']))
    except PendingNameChange.DoesNotExist:
        return HttpResponse(json.dumps({'success': False, 'error': _('Invalid ID')}))

    pnc.delete()
    return HttpResponse(json.dumps({'success': True}))


def accept_name_change_by_id(id):
    try:
        pnc = PendingNameChange.objects.get(id=id)
    except PendingNameChange.DoesNotExist:
        return HttpResponse(json.dumps({'success': False, 'error': _('Invalid ID')}))

    u = pnc.user
    up = UserProfile.objects.get(user=u)

    # Save old name
    meta = up.get_meta()
    if 'old_names' not in meta:
        meta['old_names'] = []
    meta['old_names'].append([up.name, pnc.rationale, datetime.datetime.now(UTC).isoformat()])
    up.set_meta(meta)

    up.name = pnc.new_name
    up.save()
    pnc.delete()

    return HttpResponse(json.dumps({'success': True}))


@ensure_csrf_cookie
def accept_name_change(request):
    ''' JSON: Name change process. Course staff clicks 'accept' on a given name change

    We used this during the prototype but now we simply record name changes instead
    of manually approving them. Still keeping this around in case we want to go
    back to this approval method.
    '''
    if not request.user.is_staff:
        raise Http404

    return accept_name_change_by_id(int(request.POST['id']))
