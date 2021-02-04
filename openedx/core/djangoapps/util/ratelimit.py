"""
Code to get ip from request.
"""


from ipware.ip import get_ip


def real_ip(group, request):  # lint-amnesty, pylint: disable=unused-argument
    return get_ip(request)
