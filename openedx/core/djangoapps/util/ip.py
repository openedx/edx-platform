"""
Utilities for determining the IP address of a request.


Summary
=======

For developers:

- Call ``get_safest_client_ip`` whenever you want to know the caller's IP address
- Make sure ``init_client_ips`` is called as early as possible in the middleware stack
- See the "Guidance for developers" section for more advanced usage

For site operators:

- See the "Configuration" section for important information and guidance

For everyone:

- Background information is available in the "Concepts" section


Concepts
========

- The *IP chain* is the list of IPs in the ``X-Forwarded-For`` (XFF) header followed
  by the ``REMOTE_ADDR`` value. If all involved parties are telling the truth, this
  is the list of IP addresses that have relayed the HTTP request. However, due to
  the possibility of spoofing, this raw data cannot be used directly for all
  purposes:

  - The rightmost IP in the chain is the IP that has directly connected with the
    server and sent or relayed the request. In most deployments, this is likely
    to be a reverse proxy such as nginx. In any case it is the "closest" IP (in
    the sense of the request chain, not in terms of geographic proximity.)
  - The next closest IP, if present, is the one that the closest IP *claims*
    sent the request to it. Each IP in the chain can only vouch for the
    correctness of the IP immediately to its left in the list.
  - In a normal, unspoofed request, the leftmost IP is the "real" client IP, the
    IP of the computer that made the original request.
  - However, clients can send a fake XFF header, so the leftmost IP in the chain
    cannot be trusted in the general case. In fact, the only IP that can be
    trusted absolutely is the rightmost one.
  - The challenge is to determine what the leftmost *trusted* IP is, as this is
    the most accurate we can get without compromising on security.

- The *external chain* is some prefix of the IP chain that stops before the
  (recognized) edge of the deployment's infrastructure. That is, the external
  chain is the portion of the IP chain that is to the left of some trust
  boundary, as determined by configuration or some fallback method. This is the
  list of IPs that can all plausibly be considered the "real" IP of the client.
  If the server is configured correctly this may contain, in order: Any IPs
  spoofed by the client, the client's own IP, IPs of any forwarding HTTP proxies
  specified by the client, and then IPs of any reverse HTTP proxies the
  request passed through *before* reaching the deployment's own infrastructure
  (CDN, load balancer, etc.)

  - Caveat: In the case where the request is being sent through an anonymizing
    proxy such as a VPN, the VPN's exit node IP is considered the "real" client
    IP.
  - Despite the name, this chain may contain private-range IP addresses, in
    particular if a request originates from another server in the same
    datacenter.


Guidance for developers
=======================

Almost anywhere you care about IP address, just call ``get_safest_client_ip``.
This will get you the *rightmost* IP of the external chain (defined above).
Because it cannot be easily spoofed by the caller, it is suitable for adversarial
use-cases such as:

- Rate-limiting
- Only allowing certain IPs to access a resource (or alternatively, blocking them)

In some less common situations where you need the entire external chain, you
can call ``get_all_client_ips`. This returns a list of IP addresses, although for
the great majority of normal requests this will be a list of length 1. This list is
appropriate for when you're recording IPs for manual review or need to make a
decision based on all of the IPs (no matter which one is the "real" one. This might
include:

- Audit logs
- Telling a user about other active sessions on their account
- Georestriction

In some very rare cases you might want just a single IP that isn't rightmost. In
some cases you might ask for the entire external chain and then take the leftmost
IP. This should only be used in non-adversarial situations, and is usually the wrong
choice, but may be appropriate for:

- Localization (if other HTTP headers aren't sufficient)
- Analytics


Configuration
=============

Configuration is via ``CLOSEST_CLIENT_IP_FROM_HEADERS``, which allows specifying
an HTTP header that will be trusted to report the rightmost IP in the external chain.
See setting annotation for details, but guidance on common configurations is provided
here:

- If you use a CDN as your outermost proxy:

  - Find what header your CDN sends to its origin that indicates the remote address it
    sees on inbound connections. For example, with Cloudflare this is ``CF-Connecting-IP``.
  - Ensure that your CDN always overrides this header if it exists in the inbound request,
    and never accepts a value provided by the client. Some CDNs are better than others
    about this.
  - Recommended setting, using Cloudflare as the example::

       CLOSEST_CLIENT_IP_FROM_HEADERS:
       - name: CF-Connecting-IP
         index: 0

    It would be equivalent to use ``-1`` as the index since there is always one and only
    one IP in this header, and Python list indexing rules are used here.
  - As a general rule, you should also ensure that traffic cannot bypass the CDN and reach
    your origin directly, since otherwise attackers will be able to spoof their IP address
    (and bypass protections your CDN provides). You may need to arrange for your CDN to set
    a header containing a shared secret.

- If your outermost proxy is an AWS ELB or other proxy on the same local network as your
  server, or you have any other configuration in which your proxies and application speak
  to each other using private-range IP addresses:

    - You can rely on the rightmost public IP in the IP chain to be the safest client IP.
      To do this, set your configuration for zero trusted headers::

         CLOSEST_CLIENT_IP_FROM_HEADERS: []

    - This assumes that 1) your outermost proxy always appends to ``X-Forwarded-For``, and
      2) any further proxies between that one and your application either append to it
      (ideal) or pass it along unchanged (not ideal, but workable). This is true by default
      for most proxy software.

- If you have any reverse proxy that will be seen by the next proxy or your application as
  having a public IP:

  - You'll need to rely on having a consistent *number* of proxies in front of your
    application, and you'll need to know which ones append to the ``X-Forwarded-For``
    header instead of just passing it unchanged.
  - Once you know the number of your proxies in the chain that append, you can use this
    count to say that the Nth-from-last IP in the ``X-Forwarded-For`` is the closest client
    IP. For example, if you had two, you would use ``-2`` (note the negative sign) to
    indicate the second-from-last IP::

       CLOSEST_CLIENT_IP_FROM_HEADERS:
       - name: X-Forwarded-For
         index: -2

  - This is fragile in the face of network configuration changes, so having your outermost
    proxy set a special header is preferred.
  - Configuring the proxy count too low will result in rate-limiting your own proxies;
    configuring it too high will allow attackers to bypass rate-limiting.
  - Side note: Even if you don't use it for ``CLOSEST_CLIENT_IP_FROM_HEADERS``, this
    proxy-counting approach will be required for configuring django-rest-framework's
    ``NUM_PROXIES`` setting.

- If your application is directly exposed to the public internet, without even a local proxy:

  - This is an unusual configuration, but simple to configure; with no proxies, just indicate
    that there are no trusted headers and therefore the closest public IP should be used::

       CLOSEST_CLIENT_IP_FROM_HEADERS: []
"""

import ipaddress
import warnings

from django.conf import settings
from edx_toggles.toggles import WaffleSwitch

# .. toggle_name: ip.legacy
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Emergency switch to revert to use the older, less secure method for
#   IP determination. When enabled, instructs switch's callers to revert to using the *leftmost*
#   IP from the X-Forwarded-For header. When disabled (the default), callers should use the new
#   code path for IP determination, which has callers retrieve the entire external chain or pick
#   the leftmost or rightmost IP from it. The construction of the external chain is configurable
#   via ``CLOSEST_CLIENT_IP_FROM_HEADERS``.
#     This toggle, as well as any other legacy IP references, should be deleted (in the off
#   position) when the new IP code is well-tested and all IP-reliant code has been switched over.
# .. toggle_warning: This switch does not control the behavior of this module. Callers must
#   opt into querying this switch, and can call ``get_legacy_ip`` if the switch is enabled.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-03-24
# .. toggle_target_removal_date: 2022-07-01
# .. toggle_tickets: https://openedx.atlassian.net/browse/ARCHBOM-2056 (internal only)
USE_LEGACY_IP = WaffleSwitch('ip.legacy', module_name=__name__)


def get_legacy_ip(request):
    """
    Return a client IP selected using an old, insecure method.

    Always picks the leftmost IP in the X-Forwarded-For header, if present,
    otherwise returns the original REMOTE_ADDR.
    """
    if xff := request.META.get('HTTP_X_FORWARDED_FOR'):
        return xff.split(',')[0].strip()
    else:
        # Might run before or after XForwardedForMiddleware.
        return request.META.get('ORIGINAL_REMOTE_ADDR', request.META['REMOTE_ADDR'])


def _get_meta_ip_strs(request, header_name):
    """
    Get a list of IPs from a header in the given request.

    Return the list of IPs the request is carrying on this header, which is
    expected to be comma-delimited if it contains more than one. Response
    may be an empty list for missing or empty header. List items may not be
    valid IPs.
    """
    if not header_name:
        return []

    field_name = 'HTTP_' + header_name.replace('-', '_').upper()
    header_value = request.META.get(field_name, '').strip()

    if header_value:
        return [s.strip() for s in header_value.split(',')]
    else:
        return []


def get_raw_ip_chain(request):
    """
    Retrieve the full IP chain from this request, as list of raw strings.

    This is uninterpreted and unparsed, except for splitting on commas and
    removing extraneous whitespace.
    """
    return _get_meta_ip_strs(request, 'X-Forwarded-For') + [request.META['REMOTE_ADDR']]


def _get_usable_ip_chain(request):
    """
    Retrieve the full IP chain from this request, as parsed addresses.

    The IP chain is the X-Forwarded-For header, followed by the REMOTE_ADDR.
    This list is then narrowed to the largest suffix that can be parsed as
    IP addresses.
    """
    parsed = []
    for ip_str in reversed(get_raw_ip_chain(request)):
        try:
            parsed.append(ipaddress.ip_address(ip_str))
        except ValueError:
            break
    return list(reversed(parsed))


def _remove_tail(elements, f_discard):
    """
    Remove items from the tail of the given list until f_discard returns false.

    - elements is a list
    - f_discard is a function that accepts an item from the list and returns
      true if it should be discarded from the tail

    Returns a new list that is a possibly-empty prefix of the input list.

    (This is basically itertools.dropwhile on a reversed list.)
    """
    prefix = elements[:]
    while prefix and f_discard(prefix[-1]):
        prefix.pop()
    return prefix


def _get_client_ips_via_xff(request):
    """
    Get the external chain of the request by discarding private IPs.

    This is a strategy used by ``get_all_client_ips`` and should not be used
    directly.

    Returns a list of *parsed* IP addresses, one of:

    - A list ending in a publicly routable IP
    - A list with a single, private-range IP
    - An empty list, if REMOTE_ADDR was unparseable as an IP address. This
      would be very unusual but could possibly happen if a local reverse proxy
      used a domain socket rather than a TCP connection.
    """
    ip_chain = _get_usable_ip_chain(request)
    external_chain = _remove_tail(ip_chain, lambda ip: not ip.is_global)

    # If the external_chain is in fact all private, everything will have been
    # removed. In that case, just return the leftmost IP it would have
    # considered, even though it must be a private IP.
    return external_chain or ip_chain[:1]


# .. setting_name: CLOSEST_CLIENT_IP_FROM_HEADERS
# .. setting_default: []
# .. setting_description: A list of header/index pairs to use for determining the IP in the
#   IP chain that is just outside of this deployment's infrastructure boundary -- that is,
#   the rightmost address in the IP chain that is *not* owned by the deployment. (See module
#   docstring for background and definitions, as well as guidance on configuration.)
#       Each list entry is a dict containing a header name and an index into that header. This will
#   control how the client's IP addresses are determined for attribution, tracking, rate-limiting,
#   or other general-purpose needs.
#       The named header must contain a list of IP addresses separated by commas, with whitespace
#   tolerated around each address. The index is used for a Python list lookup, e.g. 0 is the first
#   element and -2 is the second from the end.
#       Header/index pairs will be tried in turn until the first one that yields a usable IP, which
#   will then be used to determine the end of the external chain.
#       If the setting is an empty list, or if none of the entries yields a usable IP (header is
#   missing, index out of range, IP not in IP chain), then a fallback strategy will be used
#   instead: Private-range IPs will be discarded from the right of the IP chain until a public
#   IP is found, or the chain shrinks to one IP. This entry will then be considered the rightmost
#   end of the external chain.
#       Migrations from one network configuration to another may be accomplished by first adding the
#   new header to the list, making the networking change, and then removing the old one.
# .. setting_warnings: Changes to the networking configuration that are not coordinated with
#   this setting may allow callers to spoof their IP address.


def _get_trusted_header_ip(request, header_name, index):
    """
    Read a parsed IP address from a header at the specified position.

    Helper function for ``_get_client_ips_via_trusted_header``.

    Returns None if header is missing, index is out of range, or the located
    entry can't be parsed as an IP address.
    """
    ip_strs = _get_meta_ip_strs(request, header_name)

    if not ip_strs:
        warnings.warn(f"Configured IP address header was missing: {header_name!r}", UserWarning)
        return None

    try:
        trusted_ip_str = ip_strs[index]
    except IndexError:
        warnings.warn(
            "Configured index into IP address header is out of range: "
            f"{header_name!r}:{index!r} "
            f"(actual length {len(ip_strs)})",
            UserWarning
        )
        return None

    try:
        return ipaddress.ip_address(trusted_ip_str)
    except ValueError:
        warnings.warn(
            "Configured trusted IP address header contained invalid IP: "
            f"{header_name!r}:{index!r}",
            UserWarning
        )


def _get_client_ips_via_trusted_header(request):
    """
    Get the external chain by reading the trust boundary from a header.

    This is a strategy used by ``get_all_client_ips`` and should not be used
    directly. It does not implement any fallback in case of misconfiguration.

    Uses ``CLOSEST_CLIENT_IP_FROM_HEADERS`` to identify the IP just outside of
    the deployment's infrastructure boundary, and uses the rightmost position
    of this to determine where the external chain stops. See setting docs for
    more details.

    Returns one of the following:

    - A non-empty list of *parsed* IP addresses, where the rightmost IP is the
      same as the one identified in the trusted header.
    - None if no headers configured or all headers are unusable.

    A configured header can be unusable if it's missing from the request, the
    index is out of range, the indicated entry in the header can't be parsed
    as an IP address, or the IP in the header can't be found in the IP chain.
    """
    header_entries = getattr(settings, 'CLOSEST_CLIENT_IP_FROM_HEADERS', [])

    full_chain = _get_usable_ip_chain(request)
    external_chain = []

    for entry in header_entries:
        header_name = entry['name']
        index = entry['index']
        if closest_client_ip := _get_trusted_header_ip(request, header_name, index):
            # The equality check in this predicate is why we use parsed IP
            # addresses -- ::1 should compare as equal to 0:0:0:0:0:0:0:1.
            external_chain = _remove_tail(full_chain, lambda ip: ip != closest_client_ip)  # pylint: disable=cell-var-from-loop
            if external_chain:
                break
            else:
                warnings.warn(
                    f"Ignoring trusted header IP {header_name!r}:{index!r} "
                    "because it was not found in the actual IP chain.",
                    UserWarning
                )

    return external_chain


def _compute_client_ips(request):
    """
    Get the request's external chain, a non-empty list of IP address strings.

    Warning: should only be called once and cached by ``init_client_ips``.

    Prefer to use ``get_all_client_ips`` to retrieve the value stored on the
    request, unless you are sure that later middleware has not modified
    the REMOTE_ADDR in-place.

    This function will attempt several strategies to determine the external chain:

    - If ``CLOSEST_CLIENT_IP_FROM_HEADERS`` is configured and usable, it will be
      used to determine the rightmost end of the external chain (by reading a
      trusted HTTP header).
    - If that does not yield a result, fall back to assuming that the rightmost
      public IP address in the IP chain is the end of the external chain. (For an
      in-datacenter HTTP request, may instead yield a list with a private IP.)
    """
    # In practice the fallback to REMOTE_ADDR should never happen, since that
    # would require that value to be present and malformed but with no XFF
    # present.
    ips = _get_client_ips_via_trusted_header(request) \
        or _get_client_ips_via_xff(request) \
        or [request.META['REMOTE_ADDR']]

    return [str(ip) for ip in ips]


def init_client_ips(request):
    """
    Compute the request's external chain and store it in the request.

    This should be called early in the middleware stack in order to avoid
    being called after another middleware that overwrites ``REMOTE_ADDR``,
    which is a pattern some apps use.

    If called multiple times or if ``CLIENT_IPS`` is already present in
    ``request.META``, will just warn.
    """
    if 'CLIENT_IPS' in request.META:
        warnings.warn("init_client_ips refusing to overwrite existing CLIENT_IPS")
    else:
        request.META['CLIENT_IPS'] = _compute_client_ips(request)


def get_all_client_ips(request):
    """
    Get the request's external chain, a non-empty list of IP address strings.

    Most consumers of IP addresses should just use ``get_safest_client_ip``.

    Calls ``init_client_ips`` if needed.
    """
    if 'CLIENT_IPS' not in request.META:
        init_client_ips(request)

    return request.META['CLIENT_IPS']


def get_safest_client_ip(request):
    """
    Get the safest choice of client IP.

    Returns a single string containing the IP address that most likely
    represents the originator of the HTTP call, without compromising on
    safety.

    This is always the rightmost value in the external IP chain that
    is returned by ``get_all_client_ips``. See module docstring for
    more details.
    """
    return get_all_client_ips(request)[-1]
