"""
Middleware to identify the country of origin of page requests.

Middleware adds `country_code` in session.

Usage:

# To enable the Geoinfo feature on a per-view basis, use:
decorator `django.utils.decorators.decorator_from_middleware(middleware_class)`

"""
import logging
import geoip2.database

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from ipware.ip import get_client_ip
from ipware.utils import is_public_ip

log = logging.getLogger(__name__)


class CountryMiddleware(MiddlewareMixin):
    """
    Identify the country by IP address.
    """
    def process_request(self, request):
        """
        Identify the country by IP address.

        Store country code in session.
        """
        new_ip_address = get_client_ip(request)[0]
        old_ip_address = request.session.get('ip_address', None)

        if not new_ip_address and old_ip_address:
            del request.session['ip_address']
            del request.session['country_code']
        elif new_ip_address != old_ip_address and is_public_ip(new_ip_address):
            reader = geoip2.database.Reader(settings.GEOIP_PATH)
            try:
                response = reader.country(new_ip_address)
                country_code = response.country.iso_code
            except geoip2.errors.AddressNotFoundError:
                country_code = ""

            request.session['country_code'] = country_code
            request.session['ip_address'] = new_ip_address
            log.debug(u'Country code for IP: %s is set to %s', new_ip_address, country_code)
            reader.close()
