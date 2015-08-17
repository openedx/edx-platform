import functools
import json
import logging
import random
import re
import string       # pylint: disable=deprecated-module
import fnmatch
import unicodedata
import urllib

from textwrap import dedent
from external_auth.models import ExternalAuthMap
from external_auth.djangostore import DjangoOpenIDStore

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

if settings.FEATURES.get('AUTH_USE_CAS'):
    from django_cas.views import login as django_cas_login

from student.helpers import get_next_url_for_login_page
from student.models import UserProfile

from django.http import HttpResponse, HttpResponseRedirect, HttpRequest, HttpResponseForbidden
from django.utils.http import urlquote, is_safe_url
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from edxmako.shortcuts import render_to_response, render_to_string
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    from django.contrib.csrf.middleware import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie

import django_openid_auth.views as openid_views
from django_openid_auth import auth as openid_auth
from openid.consumer.consumer import SUCCESS

from openid.server.server import Server, ProtocolError, UntrustedReturnURL
from openid.server.trustroot import TrustRoot
from openid.extensions import ax, sreg
from ratelimitbackend.exceptions import RateLimitException

import student.views
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey

log = logging.getLogger("edx.external_auth")
AUDIT_LOG = logging.getLogger("audit")

SHIBBOLETH_DOMAIN_PREFIX = settings.SHIBBOLETH_DOMAIN_PREFIX
OPENID_DOMAIN_PREFIX = settings.OPENID_DOMAIN_PREFIX

# -----------------------------------------------------------------------------
# OpenID Common
# -----------------------------------------------------------------------------


@csrf_exempt
def default_render_failure(request,
                           message,
                           status=403,
                           template_name='extauth_failure.html',
                           exception=None):
    """Render an Openid error page to the user"""

    log.debug("In openid_failure " + message)

    data = render_to_string(template_name,
                            dict(message=message, exception=exception))

    return HttpResponse(data, status=status)


# -----------------------------------------------------------------------------
# OpenID Authentication
# -----------------------------------------------------------------------------


def generate_password(length=12, chars=string.letters + string.digits):
    """Generate internal password for externally authenticated user"""
    choice = random.SystemRandom().choice
    return ''.join([choice(chars) for _i in range(length)])


@csrf_exempt
def openid_login_complete(request,
                          redirect_field_name=REDIRECT_FIELD_NAME,
                          render_failure=None):
    """Complete the openid login process"""

    render_failure = (render_failure or default_render_failure)

    openid_response = openid_views.parse_openid_response(request)
    if not openid_response:
        return render_failure(request,
                              'This is an OpenID relying party endpoint.')

    if openid_response.status == SUCCESS:
        external_id = openid_response.identity_url
        oid_backend = openid_auth.OpenIDBackend()
        details = oid_backend._extract_user_details(openid_response)

        log.debug('openid success, details=%s', details)

        url = getattr(settings, 'OPENID_SSO_SERVER_URL', None)
        external_domain = "{0}{1}".format(OPENID_DOMAIN_PREFIX, url)
        fullname = '%s %s' % (details.get('first_name', ''),
                              details.get('last_name', ''))

        return _external_login_or_signup(
            request,
            external_id,
            external_domain,
            details,
            details.get('email', ''),
            fullname,
            retfun=functools.partial(redirect, get_next_url_for_login_page(request)),
        )

    return render_failure(request, 'Openid failure')


def _external_login_or_signup(request,
                              external_id,
                              external_domain,
                              credentials,
                              email,
                              fullname,
                              retfun=None):
    """Generic external auth login or signup"""
    # see if we have a map from this external_id to an edX username
    try:
        eamap = ExternalAuthMap.objects.get(external_id=external_id,
                                            external_domain=external_domain)
        log.debug(u'Found eamap=%s', eamap)
    except ExternalAuthMap.DoesNotExist:
        # go render form for creating edX user
        eamap = ExternalAuthMap(external_id=external_id,
                                external_domain=external_domain,
                                external_credentials=json.dumps(credentials))
        eamap.external_email = email
        eamap.external_name = fullname
        eamap.internal_password = generate_password()
        log.debug(u'Created eamap=%s', eamap)
        eamap.save()

    log.info(u"External_Auth login_or_signup for %s : %s : %s : %s", external_domain, external_id, email, fullname)
    uses_shibboleth = settings.FEATURES.get('AUTH_USE_SHIB') and external_domain.startswith(SHIBBOLETH_DOMAIN_PREFIX)
    uses_certs = settings.FEATURES.get('AUTH_USE_CERTIFICATES')
    internal_user = eamap.user
    if internal_user is None:
        if uses_shibboleth:
            # If we are using shib, try to link accounts
            # For Stanford shib, the email the idp returns is actually under the control of the user.
            # Since the id the idps return is not user-editable, and is of the from "username@stanford.edu",
            # use the id to link accounts instead.
            try:
                link_user = User.objects.get(email=eamap.external_id)
                if not ExternalAuthMap.objects.filter(user=link_user).exists():
                    # if there's no pre-existing linked eamap, we link the user
                    eamap.user = link_user
                    eamap.save()
                    internal_user = link_user
                    log.info(u'SHIB: Linking existing account for %s', eamap.external_id)
                    # now pass through to log in
                else:
                    # otherwise, there must have been an error, b/c we've already linked a user with these external
                    # creds
                    failure_msg = _(dedent("""
                        You have already created an account using an external login like WebAuth or Shibboleth.
                        Please contact %s for support """
                                           % getattr(settings, 'TECH_SUPPORT_EMAIL', 'techsupport@class.stanford.edu')))
                    return default_render_failure(request, failure_msg)
            except User.DoesNotExist:
                log.info(u'SHIB: No user for %s yet, doing signup', eamap.external_email)
                return _signup(request, eamap, retfun)
        else:
            log.info(u'No user for %s yet. doing signup', eamap.external_email)
            return _signup(request, eamap, retfun)

    # We trust shib's authentication, so no need to authenticate using the password again
    uname = internal_user.username
    if uses_shibboleth:
        user = internal_user
        # Assuming this 'AUTHENTICATION_BACKENDS' is set in settings, which I think is safe
        if settings.AUTHENTICATION_BACKENDS:
            auth_backend = settings.AUTHENTICATION_BACKENDS[0]
        else:
            auth_backend = 'django.contrib.auth.backends.ModelBackend'
        user.backend = auth_backend
        if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            AUDIT_LOG.info(u'Linked user.id: {0} logged in via Shibboleth'.format(user.id))
        else:
            AUDIT_LOG.info(u'Linked user "{0}" logged in via Shibboleth'.format(user.email))
    elif uses_certs:
        # Certificates are trusted, so just link the user and log the action
        user = internal_user
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            AUDIT_LOG.info(u'Linked user_id {0} logged in via SSL certificate'.format(user.id))
        else:
            AUDIT_LOG.info(u'Linked user "{0}" logged in via SSL certificate'.format(user.email))
    else:
        user = authenticate(username=uname, password=eamap.internal_password, request=request)
    if user is None:
        # we want to log the failure, but don't want to log the password attempted:
        if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            AUDIT_LOG.warning(u'External Auth Login failed')
        else:
            AUDIT_LOG.warning(u'External Auth Login failed for "{0}"'.format(uname))
        return _signup(request, eamap, retfun)

    if not user.is_active:
        if settings.FEATURES.get('BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'):
            # if BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH, we trust external auth and activate any users
            # that aren't already active
            user.is_active = True
            user.save()
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.info(u'Activating user {0} due to external auth'.format(user.id))
            else:
                AUDIT_LOG.info(u'Activating user "{0}" due to external auth'.format(uname))
        else:
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.warning(u'User {0} is not active after external login'.format(user.id))
            else:
                AUDIT_LOG.warning(u'User "{0}" is not active after external login'.format(uname))
            # TODO: improve error page
            msg = 'Account not yet activated: please look for link in your email'
            return default_render_failure(request, msg)

    login(request, user)
    request.session.set_expiry(0)

    if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
        AUDIT_LOG.info(u"Login success - user.id: {0}".format(user.id))
    else:
        AUDIT_LOG.info(u"Login success - {0} ({1})".format(user.username, user.email))
    if retfun is None:
        return redirect('/')
    return retfun()


def _flatten_to_ascii(txt):
    """
    Flattens possibly unicode txt to ascii (django username limitation)
    @param name:
    @return: the flattened txt (in the same type as was originally passed in)
    """
    if isinstance(txt, str):
        txt = txt.decode('utf-8')
        return unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore')
    else:
        return unicode(unicodedata.normalize('NFKD', txt).encode('ASCII', 'ignore'))


@ensure_csrf_cookie
def _signup(request, eamap, retfun=None):
    """
    Present form to complete for signup via external authentication.
    Even though the user has external credentials, he/she still needs
    to create an account on the edX system, and fill in the user
    registration form.

    eamap is an ExternalAuthMap object, specifying the external user
    for which to complete the signup.

    retfun is a function to execute for the return value, if immediate
    signup is used.  That allows @ssl_login_shortcut() to work.
    """
    # save this for use by student.views.create_account
    request.session['ExternalAuthMap'] = eamap

    if settings.FEATURES.get('AUTH_USE_CERTIFICATES_IMMEDIATE_SIGNUP', ''):
        # do signin immediately, by calling create_account, instead of asking
        # student to fill in form.  MIT students already have information filed.
        username = eamap.external_email.split('@', 1)[0]
        username = username.replace('.', '_')
        post_vars = dict(username=username,
                         honor_code=u'true',
                         terms_of_service=u'true')
        log.info(u'doing immediate signup for %s, params=%s', username, post_vars)
        student.views.create_account(request, post_vars)
        # should check return content for successful completion before
        if retfun is not None:
            return retfun()
        else:
            return redirect('/')

    # default conjoin name, no spaces, flattened to ascii b/c django can't handle unicode usernames, sadly
    # but this only affects username, not fullname
    username = re.sub(r'\s', '', _flatten_to_ascii(eamap.external_name), flags=re.UNICODE)

    context = {'has_extauth_info': True,
               'show_signup_immediately': True,
               'extauth_domain': eamap.external_domain,
               'extauth_id': eamap.external_id,
               'extauth_email': eamap.external_email,
               'extauth_username': username,
               'extauth_name': eamap.external_name,
               'ask_for_tos': True,
               }

    # Some openEdX instances can't have terms of service for shib users, like
    # according to Stanford's Office of General Counsel
    uses_shibboleth = (settings.FEATURES.get('AUTH_USE_SHIB') and
                       eamap.external_domain.startswith(SHIBBOLETH_DOMAIN_PREFIX))
    if uses_shibboleth and settings.FEATURES.get('SHIB_DISABLE_TOS'):
        context['ask_for_tos'] = False

    # detect if full name is blank and ask for it from user
    context['ask_for_fullname'] = eamap.external_name.strip() == ''

    # validate provided mail and if it's not valid ask the user
    try:
        validate_email(eamap.external_email)
        context['ask_for_email'] = False
    except ValidationError:
        context['ask_for_email'] = True

    log.info(u'EXTAUTH: Doing signup for %s', eamap.external_id)

    return student.views.register_user(request, extra_context=context)


# -----------------------------------------------------------------------------
# MIT SSL
# -----------------------------------------------------------------------------


def _ssl_dn_extract_info(dn_string):
    """
    Extract username, email address (may be anyuser@anydomain.com) and
    full name from the SSL DN string.  Return (user,email,fullname) if
    successful, and None otherwise.
    """
    ss = re.search('/emailAddress=(.*)@([^/]+)', dn_string)
    if ss:
        user = ss.group(1)
        email = "%s@%s" % (user, ss.group(2))
    else:
        return None
    ss = re.search('/CN=([^/]+)/', dn_string)
    if ss:
        fullname = ss.group(1)
    else:
        return None
    return (user, email, fullname)


def ssl_get_cert_from_request(request):
    """
    Extract user information from certificate, if it exists, returning (user, email, fullname).
    Else return None.
    """
    certkey = "SSL_CLIENT_S_DN"  # specify the request.META field to use

    cert = request.META.get(certkey, '')
    if not cert:
        cert = request.META.get('HTTP_' + certkey, '')
    if not cert:
        try:
            # try the direct apache2 SSL key
            cert = request._req.subprocess_env.get(certkey, '')
        except Exception:
            return ''

    return cert


def ssl_login_shortcut(fn):
    """
    Python function decorator for login procedures, to allow direct login
    based on existing ExternalAuth record and MIT ssl certificate.
    """
    def wrapped(*args, **kwargs):
        """
        This manages the function wrapping, by determining whether to inject
        the _external signup or just continuing to the internal function
        call.
        """

        if not settings.FEATURES['AUTH_USE_CERTIFICATES']:
            return fn(*args, **kwargs)
        request = args[0]

        if request.user and request.user.is_authenticated():  # don't re-authenticate
            return fn(*args, **kwargs)

        cert = ssl_get_cert_from_request(request)
        if not cert:		# no certificate information - show normal login window
            return fn(*args, **kwargs)

        def retfun():
            """Wrap function again for call by _external_login_or_signup"""
            return fn(*args, **kwargs)

        (_user, email, fullname) = _ssl_dn_extract_info(cert)
        return _external_login_or_signup(
            request,
            external_id=email,
            external_domain="ssl:MIT",
            credentials=cert,
            email=email,
            fullname=fullname,
            retfun=retfun
        )
    return wrapped


@csrf_exempt
def ssl_login(request):
    """
    This is called by branding.views.index when
    FEATURES['AUTH_USE_CERTIFICATES'] = True

    Used for MIT user authentication.  This presumes the web server
    (nginx) has been configured to require specific client
    certificates.

    If the incoming protocol is HTTPS (SSL) then authenticate via
    client certificate.  The certificate provides user email and
    fullname; this populates the ExternalAuthMap.  The user is
    nevertheless still asked to complete the edX signup.

    Else continues on with student.views.index, and no authentication.
    """
    # Just to make sure we're calling this only at MIT:
    if not settings.FEATURES['AUTH_USE_CERTIFICATES']:
        return HttpResponseForbidden()

    cert = ssl_get_cert_from_request(request)

    if not cert:
        # no certificate information - go onward to main index
        return student.views.index(request)

    (_user, email, fullname) = _ssl_dn_extract_info(cert)

    redirect_to = get_next_url_for_login_page(request)
    retfun = functools.partial(redirect, redirect_to)
    return _external_login_or_signup(
        request,
        external_id=email,
        external_domain="ssl:MIT",
        credentials=cert,
        email=email,
        fullname=fullname,
        retfun=retfun
    )


# -----------------------------------------------------------------------------
# CAS (Central Authentication Service)
# -----------------------------------------------------------------------------
def cas_login(request, next_page=None, required=False):
    """
        Uses django_cas for authentication.
        CAS is a common authentcation method pioneered by Yale.
        See http://en.wikipedia.org/wiki/Central_Authentication_Service

        Does normal CAS login then generates user_profile if nonexistent,
        and if login was successful.  We assume that user details are
        maintained by the central service, and thus an empty user profile
        is appropriate.
    """

    ret = django_cas_login(request, next_page, required)

    if request.user.is_authenticated():
        user = request.user
        if not UserProfile.objects.filter(user=user):
            user_profile = UserProfile(name=user.username, user=user)
            user_profile.save()

    return ret


# -----------------------------------------------------------------------------
# Shibboleth (Stanford and others.  Uses *Apache* environment variables)
# -----------------------------------------------------------------------------
def shib_login(request):
    """
        Uses Apache's REMOTE_USER environment variable as the external id.
        This in turn typically uses EduPersonPrincipalName
        http://www.incommonfederation.org/attributesummary.html#eduPersonPrincipal
        but the configuration is in the shibboleth software.
    """
    shib_error_msg = _(dedent(
        """
        Your university identity server did not return your ID information to us.
        Please try logging in again.  (You may need to restart your browser.)
        """))

    if not request.META.get('REMOTE_USER'):
        log.error(u"SHIB: no REMOTE_USER found in request.META")
        return default_render_failure(request, shib_error_msg)
    elif not request.META.get('Shib-Identity-Provider'):
        log.error(u"SHIB: no Shib-Identity-Provider in request.META")
        return default_render_failure(request, shib_error_msg)
    else:
        # If we get here, the user has authenticated properly
        shib = {attr: request.META.get(attr, '').decode('utf-8')
                for attr in ['REMOTE_USER', 'givenName', 'sn', 'mail', 'Shib-Identity-Provider', 'displayName']}

        # Clean up first name, last name, and email address
        # TODO: Make this less hardcoded re: format, but split will work
        # even if ";" is not present, since we are accessing 1st element
        shib['sn'] = shib['sn'].split(";")[0].strip().capitalize()
        shib['givenName'] = shib['givenName'].split(";")[0].strip().capitalize()

    # TODO: should we be logging creds here, at info level?
    log.info(u"SHIB creds returned: %r", shib)

    fullname = shib['displayName'] if shib['displayName'] else u'%s %s' % (shib['givenName'], shib['sn'])

    redirect_to = get_next_url_for_login_page(request)
    retfun = functools.partial(_safe_postlogin_redirect, redirect_to, request.get_host())

    return _external_login_or_signup(
        request,
        external_id=shib['REMOTE_USER'],
        external_domain=SHIBBOLETH_DOMAIN_PREFIX + shib['Shib-Identity-Provider'],
        credentials=shib,
        email=shib['mail'],
        fullname=fullname,
        retfun=retfun
    )


def _safe_postlogin_redirect(redirect_to, safehost, default_redirect='/'):
    """
    If redirect_to param is safe (not off this host), then perform the redirect.
    Otherwise just redirect to '/'.
    Basically copied from django.contrib.auth.views.login
    @param redirect_to: user-supplied redirect url
    @param safehost: which host is safe to redirect to
    @return: an HttpResponseRedirect
    """
    if is_safe_url(url=redirect_to, host=safehost):
        return redirect(redirect_to)
    return redirect(default_redirect)


def course_specific_login(request, course_id):
    """
       Dispatcher function for selecting the specific login method
       required by the course
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = modulestore().get_course(course_key)
    if not course:
        # couldn't find the course, will just return vanilla signin page
        return redirect_with_get('signin_user', request.GET)

    # now the dispatching conditionals.  Only shib for now
    if (
        settings.FEATURES.get('AUTH_USE_SHIB') and
        course.enrollment_domain and
        course.enrollment_domain.startswith(SHIBBOLETH_DOMAIN_PREFIX)
    ):
        return redirect_with_get('shib-login', request.GET)

    # Default fallthrough to normal signin page
    return redirect_with_get('signin_user', request.GET)


def course_specific_register(request, course_id):
    """
        Dispatcher function for selecting the specific registration method
        required by the course
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = modulestore().get_course(course_key)

    if not course:
        # couldn't find the course, will just return vanilla registration page
        return redirect_with_get('register_user', request.GET)

    # now the dispatching conditionals.  Only shib for now
    if (
        settings.FEATURES.get('AUTH_USE_SHIB') and
        course.enrollment_domain and
        course.enrollment_domain.startswith(SHIBBOLETH_DOMAIN_PREFIX)
    ):
        # shib-login takes care of both registration and login flows
        return redirect_with_get('shib-login', request.GET)

    # Default fallthrough to normal registration page
    return redirect_with_get('register_user', request.GET)


def redirect_with_get(view_name, get_querydict, do_reverse=True):
    """
        Helper function to carry over get parameters across redirects
        Using urlencode(safe='/') because the @login_required decorator generates 'next' queryparams with '/' unencoded
    """
    if do_reverse:
        url = reverse(view_name)
    else:
        url = view_name
    if get_querydict:
        return redirect("%s?%s" % (url, get_querydict.urlencode(safe='/')))
    return redirect(view_name)


# -----------------------------------------------------------------------------
# OpenID Provider
# -----------------------------------------------------------------------------


def get_xrds_url(resource, request):
    """
    Return the XRDS url for a resource
    """
    host = request.get_host()

    location = host + '/openid/provider/' + resource + '/'

    if request.is_secure():
        return 'https://' + location
    else:
        return 'http://' + location


def add_openid_simple_registration(request, response, data):
    sreg_data = {}
    sreg_request = sreg.SRegRequest.fromOpenIDRequest(request)
    sreg_fields = sreg_request.allRequestedFields()

    # if consumer requested simple registration fields, add them
    if sreg_fields:
        for field in sreg_fields:
            if field == 'email' and 'email' in data:
                sreg_data['email'] = data['email']
            elif field == 'fullname' and 'fullname' in data:
                sreg_data['fullname'] = data['fullname']
            elif field == 'nickname' and 'nickname' in data:
                sreg_data['nickname'] = data['nickname']

        # construct sreg response
        sreg_response = sreg.SRegResponse.extractResponse(sreg_request,
                                                          sreg_data)
        sreg_response.toMessage(response.fields)


def add_openid_attribute_exchange(request, response, data):
    try:
        ax_request = ax.FetchRequest.fromOpenIDRequest(request)
    except ax.AXError:
        #  not using OpenID attribute exchange extension
        pass
    else:
        ax_response = ax.FetchResponse()

        # if consumer requested attribute exchange fields, add them
        if ax_request and ax_request.requested_attributes:
            for type_uri in ax_request.requested_attributes.iterkeys():
                email_schema = 'http://axschema.org/contact/email'
                name_schema = 'http://axschema.org/namePerson'
                if type_uri == email_schema and 'email' in data:
                    ax_response.addValue(email_schema, data['email'])
                elif type_uri == name_schema and 'fullname' in data:
                    ax_response.addValue(name_schema, data['fullname'])

            # construct ax response
            ax_response.toMessage(response.fields)


def provider_respond(server, request, response, data):
    """
    Respond to an OpenID request
    """
    # get and add extensions
    add_openid_simple_registration(request, response, data)
    add_openid_attribute_exchange(request, response, data)

    # create http response from OpenID response
    webresponse = server.encodeResponse(response)
    http_response = HttpResponse(webresponse.body)
    http_response.status_code = webresponse.code

    # add OpenID headers to response
    for k, v in webresponse.headers.iteritems():
        http_response[k] = v

    return http_response


def validate_trust_root(openid_request):
    """
    Only allow OpenID requests from valid trust roots
    """

    trusted_roots = getattr(settings, 'OPENID_PROVIDER_TRUSTED_ROOT', None)

    if not trusted_roots:
        # not using trusted roots
        return True

    # don't allow empty trust roots
    if (not hasattr(openid_request, 'trust_root') or
            not openid_request.trust_root):
        log.error('no trust_root')
        return False

    # ensure trust root parses cleanly (one wildcard, of form *.foo.com, etc.)
    trust_root = TrustRoot.parse(openid_request.trust_root)
    if not trust_root:
        log.error('invalid trust_root')
        return False

    # don't allow empty return tos
    if (not hasattr(openid_request, 'return_to') or
            not openid_request.return_to):
        log.error('empty return_to')
        return False

    # ensure return to is within trust root
    if not trust_root.validateURL(openid_request.return_to):
        log.error('invalid return_to')
        return False

    # check that the root matches the ones we trust
    if not any(r for r in trusted_roots if fnmatch.fnmatch(trust_root, r)):
        log.error('non-trusted root')
        return False

    return True


@csrf_exempt
def provider_login(request):
    """
    OpenID login endpoint
    """

    # make and validate endpoint
    endpoint = get_xrds_url('login', request)
    if not endpoint:
        return default_render_failure(request, "Invalid OpenID request")

    # initialize store and server
    store = DjangoOpenIDStore()
    server = Server(store, endpoint)

    # first check to see if the request is an OpenID request.
    # If so, the client will have specified an 'openid.mode' as part
    # of the request.
    querydict = dict(request.REQUEST.items())
    error = False
    if 'openid.mode' in request.GET or 'openid.mode' in request.POST:
        # decode request
        try:
            openid_request = server.decodeRequest(querydict)
        except (UntrustedReturnURL, ProtocolError):
            openid_request = None

        if not openid_request:
            return default_render_failure(request, "Invalid OpenID request")

        # don't allow invalid and non-trusted trust roots
        if not validate_trust_root(openid_request):
            return default_render_failure(request, "Invalid OpenID trust root")

        # checkid_immediate not supported, require user interaction
        if openid_request.mode == 'checkid_immediate':
            return provider_respond(server, openid_request,
                                    openid_request.answer(False), {})

        # checkid_setup, so display login page
        # (by falling through to the provider_login at the
        # bottom of this method).
        elif openid_request.mode == 'checkid_setup':
            if openid_request.idSelect():
                # remember request and original path
                request.session['openid_setup'] = {
                    'request': openid_request,
                    'url': request.get_full_path(),
                    'post_params': request.POST,
                }

                # user failed login on previous attempt
                if 'openid_error' in request.session:
                    error = True
                    del request.session['openid_error']

        # OpenID response
        else:
            return provider_respond(server, openid_request,
                                    server.handleRequest(openid_request), {})

    # handle login redirection:  these are also sent to this view function,
    # but are distinguished by lacking the openid mode.  We also know that
    # they are posts, because they come from the popup
    elif request.method == 'POST' and 'openid_setup' in request.session:
        # get OpenID request from session
        openid_setup = request.session['openid_setup']
        openid_request = openid_setup['request']
        openid_request_url = openid_setup['url']
        post_params = openid_setup['post_params']
        # We need to preserve the parameters, and the easiest way to do this is
        # through the URL
        url_post_params = {
            param: post_params[param] for param in post_params if param.startswith('openid')
        }

        encoded_params = urllib.urlencode(url_post_params)

        if '?' not in openid_request_url:
            openid_request_url = openid_request_url + '?' + encoded_params
        else:
            openid_request_url = openid_request_url + '&' + encoded_params

        del request.session['openid_setup']

        # don't allow invalid trust roots
        if not validate_trust_root(openid_request):
            return default_render_failure(request, "Invalid OpenID trust root")

        # check if user with given email exists
        # Failure is redirected to this method (by using the original URL),
        # which will bring up the login dialog.
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            request.session['openid_error'] = True
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.warning("OpenID login failed - Unknown user email")
            else:
                msg = "OpenID login failed - Unknown user email: {0}".format(email)
                AUDIT_LOG.warning(msg)
            return HttpResponseRedirect(openid_request_url)

        # attempt to authenticate user (but not actually log them in...)
        # Failure is again redirected to the login dialog.
        username = user.username
        password = request.POST.get('password', None)
        try:
            user = authenticate(username=username, password=password, request=request)
        except RateLimitException:
            AUDIT_LOG.warning('OpenID - Too many failed login attempts.')
            return HttpResponseRedirect(openid_request_url)

        if user is None:
            request.session['openid_error'] = True
            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.warning("OpenID login failed - invalid password")
            else:
                msg = "OpenID login failed - password for {0} is invalid".format(email)
                AUDIT_LOG.warning(msg)
            return HttpResponseRedirect(openid_request_url)

        # authentication succeeded, so fetch user information
        # that was requested
        if user is not None and user.is_active:
            # remove error from session since login succeeded
            if 'openid_error' in request.session:
                del request.session['openid_error']

            if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
                AUDIT_LOG.info("OpenID login success - user.id: {0}".format(user.id))
            else:
                AUDIT_LOG.info("OpenID login success - {0} ({1})".format(
                               user.username, user.email))

            # redirect user to return_to location
            url = endpoint + urlquote(user.username)
            response = openid_request.answer(True, None, url)

            # Note too that this is hardcoded, and not really responding to
            # the extensions that were registered in the first place.
            results = {
                'nickname': user.username,
                'email': user.email,
                'fullname': user.profile.name,
            }

            # the request succeeded:
            return provider_respond(server, openid_request, response, results)

        # the account is not active, so redirect back to the login page:
        request.session['openid_error'] = True
        if settings.FEATURES['SQUELCH_PII_IN_LOGS']:
            AUDIT_LOG.warning("Login failed - Account not active for user.id {0}".format(user.id))
        else:
            msg = "Login failed - Account not active for user {0}".format(username)
            AUDIT_LOG.warning(msg)
        return HttpResponseRedirect(openid_request_url)

    # determine consumer domain if applicable
    return_to = ''
    if 'openid.return_to' in request.REQUEST:
        return_to = request.REQUEST['openid.return_to']
        matches = re.match(r'\w+:\/\/([\w\.-]+)', return_to)
        return_to = matches.group(1)

    # display login page
    response = render_to_response('provider_login.html', {
        'error': error,
        'return_to': return_to
    })

    # add custom XRDS header necessary for discovery process
    response['X-XRDS-Location'] = get_xrds_url('xrds', request)
    return response


def provider_identity(request):
    """
    XRDS for identity discovery
    """

    response = render_to_response('identity.xml',
                                  {'url': get_xrds_url('login', request)},
                                  mimetype='text/xml')

    # custom XRDS header necessary for discovery process
    response['X-XRDS-Location'] = get_xrds_url('identity', request)
    return response


def provider_xrds(request):
    """
    XRDS for endpoint discovery
    """

    response = render_to_response('xrds.xml',
                                  {'url': get_xrds_url('login', request)},
                                  mimetype='text/xml')

    # custom XRDS header necessary for discovery process
    response['X-XRDS-Location'] = get_xrds_url('xrds', request)
    return response
