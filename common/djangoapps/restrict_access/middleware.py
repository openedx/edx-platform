"""
Middleware to restrict access by ip addresses, which is configurable in
settings.

Usage
~~~~~

To use, find ``MIDDLEWARE_CLASSES`` in your ``settings.py`` and add:

    MIDDLEWARE_CLASSES = [
        ...
        'restrict_access.middleware.RestrictAccessMiddleware',
        ...
    ]


To enable this feature, set 'RESTRICT_ACCESS_ALLOW' in your settings.py:

  RESTRICT_ACCESS_ALLOW: tuple of ip addresses or networks allowed to access the lms.

NOTE: if there is no 'RESTRICT_ACCESS_ALLOW' in settings, the feature is considered disabled. The
middleware will allow all requests.

Additionnal settings:

  RESTRICT_ACCESS_DENY: tuple of ip addresses or networks that are excluded from
  the ALLOW list. The deny rules have priority over the allow rules.

  RESTRICT_ACCESS_REDIRECT_URL: External url used for http redirection when a request is denied.

Examples:

RESTRICT_ACCESS_ALLOW = (
    '10.0.2.0/24', # network 10.0.2.* is allowed
    '10.0.3.5'     # single ip address
    )
RESTRICT_ACCESS_DENY = (
    '10.0.2.1/32', # 10.0.2.1 ip is deny
    )
RESTRICT_ACCESS_REDIRECT_URL = 'http://code.edx.org/'

"""

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
import ipaddr

class RestrictAccessMiddleware(object):
    """
    Middleware class to control the access by ip addresses.
    """

    def process_request(self, request):

        # authenticated users are allowed
        if hasattr(request, "user") and request.user.is_authenticated():
            return

        allow = getattr(settings, "RESTRICT_ACCESS_ALLOW", None)

        # enabled?
        if allow:

            deny = getattr(settings, "RESTRICT_ACCESS_DENY", None)

            # read the ip addresses/networks settings
            try:
                request_addr = ipaddr.IPAddress(self.get_client_ip(request))
                networks_allowed = [ipaddr.IPNetwork(network) for network in allow]
                if deny:
                    networks_denied = [ipaddr.IPNetwork(network) for network in deny]
            except ValueError:
                # default policy is forbidden if we can't get the request ip
                # or the settings are invalid (ie. bad ip address or network)
                return self.deny_request()

            # default policy is denied
            request_is_allowed = False

            # loop through the settings to check if the request is allowed
            for network_allowed in networks_allowed:
                if network_allowed.Contains(request_addr):
                    request_is_allowed = True
                    if deny:
                        for network_denied in networks_denied:
                            if network_denied.Contains(request_addr):
                                request_is_allowed = False
                                break
                    break

            if not request_is_allowed:
                return self.deny_request()


    def get_client_ip(self, request):
        """
        Get the real client ip. Useful when deployed behing a proxy.
        """

        addr = request.META['REMOTE_ADDR']

        # code from http://www.djangobook.com/en/2.0/chapter17.html
        try:
            real_ip = request.META['HTTP_X_FORWARDED_FOR']
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # Take just the first one.
            addr = real_ip.split(",")[0]

        return addr

    def deny_request(self):
        """
        Deny the request. If 'RESTRICT_ACCESS_REDIRECT_URL' is defined, redirect to
        the specified url. Otherwise, return HttpResponseForbidden.
        """
        url = getattr(settings, "RESTRICT_ACCESS_REDIRECT_URL", None)
        if url:
            return HttpResponseRedirect(url)

        return HttpResponseForbidden('Access Denied')
