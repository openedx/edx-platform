"""
Code to get ip from request.
"""
from __future__ import absolute_import

from ipware.ip import get_ip


def real_ip(group, request):
    return get_ip(request)
