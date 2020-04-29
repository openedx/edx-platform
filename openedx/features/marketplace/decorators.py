from django.http import HttpResponseForbidden


def has_affiliated_user(function=None):
    def inner(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.extended_profile.organization:
            return function(request, *args, **kwargs)
        return HttpResponseForbidden('Access denied!')

    return inner
