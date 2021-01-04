"""
Code to get ip from request.
"""


from ipware.ip import get_ip


def real_ip(group, request):
    return get_ip(request)
