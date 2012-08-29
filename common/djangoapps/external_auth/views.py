import functools
import json
import logging
import random
import re
import string
import fnmatch

from external_auth.models import ExternalAuthMap

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.models import User
from student.models import UserProfile

from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import urlquote
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response, render_to_string
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    from django.contrib.csrf.middleware import csrf_exempt
from django_future.csrf import ensure_csrf_cookie
from util.cache import cache_if_anonymous

import django_openid_auth.views as openid_views
from django_openid_auth import auth as openid_auth
from openid.consumer.consumer import SUCCESS

from openid.server.server import Server
from openid.server.trustroot import TrustRoot
from openid.store.filestore import FileOpenIDStore
from openid.extensions import ax, sreg

import student.views as student_views

log = logging.getLogger("mitx.external_auth")


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


def edXauth_generate_password(length=12, chars=string.letters + string.digits):
    """Generate internal password for externally authenticated user"""
    return ''.join([random.choice(chars) for i in range(length)])


@csrf_exempt
def edXauth_openid_login_complete(request,
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

        log.debug('openid success, details=%s' % details)

        url = getattr(settings, 'OPENID_SSO_SERVER_URL', None)
        external_domain = "openid:%s" % url
        fullname = '%s %s' % (details.get('first_name', ''),
                              details.get('last_name', ''))

        return edXauth_external_login_or_signup(request,
                                                external_id,
                                                external_domain,
                                                details,
                                                details.get('email', ''),
                                                fullname)

    return render_failure(request, 'Openid failure')


def edXauth_external_login_or_signup(request,
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
        log.debug('Found eamap=%s' % eamap)
    except ExternalAuthMap.DoesNotExist:
        # go render form for creating edX user
        eamap = ExternalAuthMap(external_id=external_id,
                                external_domain=external_domain,
                                external_credentials=json.dumps(credentials))
        eamap.external_email = email
        eamap.external_name = fullname
        eamap.internal_password = edXauth_generate_password()
        log.debug('Created eamap=%s' % eamap)

        eamap.save()

    internal_user = eamap.user
    if internal_user is None:
        log.debug('No user for %s yet, doing signup' % eamap.external_email)
        return edXauth_signup(request, eamap)

    uname = internal_user.username
    user = authenticate(username=uname, password=eamap.internal_password)
    if user is None:
        log.warning("External Auth Login failed for %s / %s" %
                    (uname, eamap.internal_password))
        return edXauth_signup(request, eamap)

    if not user.is_active:
        log.warning("User %s is not active" % (uname))
        # TODO: improve error page
        msg = 'Account not yet activated: please look for link in your email'
        return default_render_failure(request, msg)

    login(request, user)
    request.session.set_expiry(0)
    student_views.try_change_enrollment(request)
    log.info("Login success - {0} ({1})".format(user.username, user.email))
    if retfun is None:
        return redirect('/')
    return retfun()


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

    # save this for use by student.views.create_account
    request.session['ExternalAuthMap'] = eamap

    # default conjoin name, no spaces
    username = eamap.external_name.replace(' ', '')

    context = {'has_extauth_info': True,
               'show_signup_immediately': True,
               'extauth_email': eamap.external_email,
               'extauth_username': username,
               'extauth_name': eamap.external_name,
               }

    log.debug('Doing signup for %s' % eamap.external_email)

    return student_views.index(request, extra_context=context)


# -----------------------------------------------------------------------------
# MIT SSL
# -----------------------------------------------------------------------------


def ssl_dn_extract_info(dn):
    """
    Extract username, email address (may be anyuser@anydomain.com) and
    full name from the SSL DN string.  Return (user,email,fullname) if
    successful, and None otherwise.
    """
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
    This is called by student.views.index when
    MITX_FEATURES['AUTH_USE_MIT_CERTIFICATES'] = True

    Used for MIT user authentication.  This presumes the web server
    (nginx) has been configured to require specific client
    certificates.

    If the incoming protocol is HTTPS (SSL) then authenticate via
    client certificate.  The certificate provides user email and
    fullname; this populates the ExternalAuthMap.  The user is
    nevertheless still asked to complete the edX signup.

    Else continues on with student.views.index, and no authentication.
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
            pass
    if not cert:
        # no certificate information - go onward to main index
        return student_views.index(request)

    (user, email, fullname) = ssl_dn_extract_info(cert)

    retfun = functools.partial(student_views.index, request)
    return edXauth_external_login_or_signup(request,
                                            external_id=email,
                                            external_domain="ssl:MIT",
                                            credentials=cert,
                                            email=email,
                                            fullname=fullname,
                                            retfun=retfun)


# -----------------------------------------------------------------------------
# OpenID Provider
# -----------------------------------------------------------------------------


def get_dict_for_openid(data):
    """
    Return a dictionary suitable for the OpenID library
    """

    return dict((k, v) for k, v in data.iteritems())


def get_xrds_url(resource, request):
    """
    Return the XRDS url for a resource
    """

    location = request.META['HTTP_HOST'] + '/openid/provider/' + resource + '/'
    if request.is_secure():
        url = 'https://' + location
    else:
        url = 'http://' + location

    return url


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

    if trusted_roots is None:
        log.debug('not using trusted roots')
        # not using trusted roots
        return True

    log.debug('validating trusted roots')

    # don't allow empty trust roots
    if (not hasattr(openid_request, 'trust_root') or
            openid_request.trust_root is None):
        log.debug('no trust_root')
        return False

    # ensure trust root parses cleanly (one wildcard, of form *.foo.com, etc.)
    trust_root = TrustRoot.parse(openid_request.trust_root)
    if trust_root is None:
        log.debug('invalid trust_root')
        return False

    # don't allow empty return tos
    if (not hasattr(openid_request, 'return_to') or
            openid_request.return_to is None):
        log.debug('empty return_to')
        return False

    # ensure return to is within trust root
    if not trust_root.validateURL(openid_request.return_to):
        log.debug('invalid return_to')
        return False

    # check that the root matches the ones we trust
    if not any(r for r in trusted_roots if fnmatch.fnmatch(trust_root, r)):
        log.debug('non-trusted root')
        return False

    return True


@csrf_exempt
def provider_login(request):
    """
    OpenID login endpoint
    """

    # initialize store and server
    endpoint = get_xrds_url('login', request)
    store = FileOpenIDStore('/tmp/openid_provider')
    server = Server(store, endpoint)

    # handle OpenID request
    query = get_dict_for_openid(request.REQUEST)
    error = False
    if 'openid.mode' in request.GET or 'openid.mode' in request.POST:
        # decode request
        openid_request = server.decodeRequest(query)

        # don't allow invalid and non-trusted trust roots
        if not validate_trust_root(openid_request):
            return default_render_failure(request, "Invalid OpenID trust root")

        # checkid_immediate not supported, require user interaction
        if openid_request.mode == 'checkid_immediate':
            return provider_respond(server, openid_request,
                                    openid_request.answer(False), {})

        # checkid_setup, so display login page
        elif openid_request.mode == 'checkid_setup':
            if openid_request.idSelect():
                # remember request and original path
                request.session['openid_request'] = {
                    'request': openid_request,
                    'url': request.get_full_path()
                }

                # user failed login on previous attempt
                if 'openid_error' in request.session:
                    error = True
                    del request.session['openid_error']

        # OpenID response
        else:
            return provider_respond(server, openid_request,
                                    server.handleRequest(openid_request), {})

    # handle login
    if request.method == 'POST' and 'openid_request' in request.session:
        # get OpenID request from session
        openid_request = request.session['openid_request']
        del request.session['openid_request']

        # don't allow invalid and non-*.cs50.net trust roots
        if not validate_trust_root(openid_request):
            return default_render_failure(request, "Invalid OpenID trust root")

        # check if user with given email exists
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            request.session['openid_error'] = True
            msg = "OpenID login failed - Unknown user email: {0}".format(email)
            log.warning(msg)
            return HttpResponseRedirect(openid_request['url'])

        # attempt to authenticate user
        username = user.username
        password = request.POST.get('password', None)
        user = authenticate(username=username, password=password)
        if user is None:
            request.session['openid_error'] = True
            msg = "OpenID login failed - password for {0} is invalid"
            msg = msg.format(email)
            log.warning(msg)
            return HttpResponseRedirect(openid_request['url'])

        # authentication succeeded, so log user in
        if user is not None and user.is_active:
            # remove error from session since login succeeded
            if 'openid_error' in request.session:
                del request.session['openid_error']

            # fullname field comes from user profile
            profile = UserProfile.objects.get(user=user)
            log.info("OpenID login success - {0} ({1})".format(user.username,
                                                               user.email))

            # redirect user to return_to location
            url = endpoint + urlquote(user.username)
            response = openid_request['request'].answer(True, None, url)

            return provider_respond(server,
                                    openid_request['request'],
                                    response,
                                    {
                                        'fullname': profile.name,
                                        'email': user.email
                                    })

        request.session['openid_error'] = True
        msg = "Login failed - Account not active for user {0}".format(username)
        log.warning(msg)
        return HttpResponseRedirect(openid_request['url'])

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

    # custom XRDS header necessary for discovery process
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
