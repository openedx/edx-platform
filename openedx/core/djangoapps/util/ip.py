"""
Utilities for determining the IP address of a request.

``get_client_ip`` is the main function of interest.
"""

import ipaddress
import warnings

from django.conf import settings


def get_meta_ips(request_meta, header_name):
    """
    Return the list of IPs the request is carrying on this header, which is
    expected to be comma-delimited if it contains more than one. Response
    may be an empty list for missing or empty header. List items may not be
    valid IPs.
    """
    if not header_name:
        return []

    field_name = 'HTTP_' + header_name.replace('-', '_').upper()
    header_value = request_meta.get(field_name, '').strip()

    if header_value:
        return [s.strip() for s in header_value.split(',')]
    else:
        return []


def get_client_ip_by_one_header(request_meta, header_name, index):
    """
    Implementation of ``get_client_ip_via_configured_header`` for one header.
    Returns None if header name and index can't be used.
    """
    ip_strs = get_meta_ips(request_meta, header_name)

    if not ip_strs:
        warnings.warn(f"Configured IP address header was missing: {header_name!r}", UserWarning)
        return None

    try:
        return ip_strs[index]
    except IndexError:
        warnings.warn(
            "Configured index into IP address header is out of range: "
            f"{header_name!r}:{index!r} "
            f"(actual length {len(ip_strs)})",
            UserWarning
        )
        return None


# .. setting_name: CLIENT_IP_HEADERS
# .. setting_default: []
# .. setting_description: A list of header/index pairs to use for determining the client's IP
#   address. Each entry is a map like ``{'name': 'X-Forwarded-For', 'index': -2}``. This will
#   control how the client's IP address is determined for attribution, tracking, rate-limiting,
#   or other general-purpose needs.
#
#   The named header must contain a list of IP addresses separated by commas, with whitespace
#   tolerated around each address. (The list must contain at least one address.) The index is
#   used for a Python list lookup, e.g. 0 is the first element and -2 is the second from the end.
#   Header/index pairs will be tried in turn and if none yields a result (header missing or index
#   out of range) or the list is empty, then the client IP will instead be drawn from
#   ``X-Forwarded-For`` and ``REMOTE_ADDR``.
#
#   Deployers using a single local proxy (e.g. a Tutor installation with caddy acting as reverse
#   proxy, and the LMS or CMS otherwise directly exposed to the internet) will likely be fine
#   with the default behavior.
#
#   For deployments behind a CDN, there may be a CDN-specific header to use. For example,
#   Cloudflare provides ``CF-Connecting-IP``. In this case, a setting of
#   ``[{'name': 'CF-Connecting-IP', 'index': 0}]`` would be the most appropriate choice.
#
#   Migrations from one network configuration to another may be accomplished by first adding the
#   new header to the list, making the networking change, and then removing the old one.
# .. setting_warnings: Changes to the networking configuration that are not coordinated with
#   this setting may allow callers to spoof their IP address.


def get_client_ip_via_configured_headers(request_meta):
    """
    Get the client IP by using first usable ``CLIENT_IP_HEADERS`` lookup.
    Return None if headers all missing or indexes are out of range (or no
    headers configured.)
    """
    for entry in getattr(settings, 'CLIENT_IP_HEADERS', []):
        if client_ip := get_client_ip_by_one_header(request_meta, entry['name'], entry['index']):
            return client_ip
    return None


def conservatively_pick_client_ip(chain):
    """
    Given a list of (maybe) IP addresses, walk from right to left and pick
    the one most likely to be the client's IP address.

    - Does not trust that any public IP is an honest proxy (meaning, a proxy
      which will honestly set or append to X-Forwarded-For).
    - Tries to find the first public IP but will return a private IP if no
      public IPs are found.
    - Returns None if an invalid IP is encountered before the first
      valid one.
    """
    chain = chain[:]  # copy to allow mutation

    # The last IP address we saw, and which we consider as the
    # conservatively correct choice unless something better comes up.
    #
    # This is a parsed IP. We'll stringify it before returning. This
    # avoids parser-confusion problems where the decider (this code)
    # and the actor (relying code) work with different interpretations
    # of any malformed data.
    current_ip = None

    while len(chain) > 0:
        try:
            next_ip = ipaddress.ip_address(chain.pop())
        except ValueError:
            # Failed to parse! So, return the current one, even if
            # it's suboptimal. This could actually be a perfectly fine
            # IP.  Perhaps the server is directly exposed to the
            # internet (REMOTE_ADDR is a public IP) and the client
            # sends in a garbage XFF.
            return current_ip and str(current_ip)

        if next_ip.is_global:
            # Lacking any knowledge of trusted proxies and other network
            # configuration, the first public IP we find is the best we
            # can do.
            return str(next_ip)
        else:
            # If we're still seeing private-space IPs, keep walking;
            # maybe we'll find a public one! But keep hold of this as
            # "current"; we may need to fall back to this if the next
            # one just turns out to be garbage.
            current_ip = next_ip

    # Ran off the front of the list, so go with what we have. This
    # would have to be a private IP, or None if the list was in fact
    # empty to begin with.
    return current_ip and str(current_ip)


def get_client_ip_via_xff(request_meta):
    """
    Get the most likely client IP from the X-Forwarded-For chain, conservatively.

    Pick the first publicly routable IP seen while walking from right to left
    (starting with REMOTE_ADDR), unless the list is exhausted or an invalid IP
    is found, in which case use the last IP before that.
    """
    # The REMOTE_ADDR is implicitly the beginning of the XFF chain
    # (this is what we would attach if we were a proxy!), so add it on
    # explicitly.  This is the IP address we can always rely on
    # having. If we're behind a proxy it may be a private IP, and if
    # we're serving directly to the internet then it may well be the
    # client IP.
    full_chain = get_meta_ips(request_meta, 'X-Forwarded-For') + [request_meta['REMOTE_ADDR']]
    chosen_ip = conservatively_pick_client_ip(full_chain)

    # In practice this fallback should never happen, since it would require
    # REMOTE_ADDR (at the end of the chain above) to be malformed.
    return chosen_ip or request_meta['REMOTE_ADDR']


def get_client_ip(request):
    """
    Determine the IP address of the HTTP client by walking the X-Forwarded-For
    header, unless there's a configured override.
    """
    # Restore the original REMOTE_ADDR since it's needed for IP determination.
    # Once XForwardedForMiddleware is no longer overwriting REMOTE_ADDR this
    # rewriting can be removed.
    #
    # This is also the reason all the other functions in this module take a
    # request.META -- it's easier to pass in an altered META dict than an
    # altered request, and this keeps the ORIGINAL_REMOTE_ADDR pollution out
    # of the other code, making it marginally more reusable.
    request_meta = request.META.copy()
    if 'ORIGINAL_REMOTE_ADDR' in request_meta:
        request_meta['REMOTE_ADDR'] = request_meta['ORIGINAL_REMOTE_ADDR']

    return get_client_ip_via_configured_headers(request_meta) or get_client_ip_via_xff(request_meta)
