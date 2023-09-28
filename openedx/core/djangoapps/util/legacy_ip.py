"""
Utilities for migrating to safer IP address determination.

This module used to contain utilities for reading the IP addresses of
a request, but those have since moved ``edx_django_utils.ip``.

What remains are the "legacy IP" utils, which should be used only
temporarily when switching a piece of code from using the leftmost IP
(legacy IP) to using the safest IP or full public IP chain (using
edx-django-utils).
"""

from edx_toggles.toggles import WaffleSwitch

# .. toggle_name: ip.legacy
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Emergency switch to revert to use an older, less secure method for
#   IP determination (instead of the newer, safer code in ``edx_django_utils.ip``).
#   When enabled, instructs switch's callers to revert to using the *leftmost*
#   IP from the X-Forwarded-For header. When disabled (the default), callers should use the new
#   code path for IP determination, which has callers retrieve the entire external chain or pick
#   the leftmost or rightmost IP from it. The construction of the external chain is configurable
#   via ``CLOSEST_CLIENT_IP_FROM_HEADERS``.
#     This toggle, as well as any other legacy IP references, should be deleted (in the off
#   position) when the new IP code is well-tested and all IP-reliant code has been switched over
#   to using ``edx_django_utils.ip``.
# .. toggle_warning: This switch does not globally control handling of IP addresses; it only
#   affects code that is explicitly querying the switch and using ``get_legacy_ip``.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-03-24
# .. toggle_target_removal_date: 2023-01-01
# .. toggle_tickets: https://2u-internal.atlassian.net/browse/ARCHBOM-2056 (internal only)
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
