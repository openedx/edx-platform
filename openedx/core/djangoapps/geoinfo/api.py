"""
Simple Python API to identify the country of origin of page requests.
"""

import geoip2.database
from django.conf import settings


def country_code_from_ip(ip_addr: str) -> str:
    """
    Return the country code associated with an IP address.
    Handles both IPv4 and IPv6 addresses.

    Args:
        ip_addr: The IP address to look up.

    Returns:
        A 2-letter country code,
        or an empty string if lookup failed.
    """
    reader = geoip2.database.Reader(settings.GEOIP_PATH)
    try:
        response = reader.country(ip_addr)
        # pylint: disable=no-member
        country_code = response.country.iso_code
    except geoip2.errors.AddressNotFoundError:
        country_code = ""
    reader.close()
    return country_code
