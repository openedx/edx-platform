from django.http import HttpResponseRedirect
from django.urls import reverse


def has_affiliated_user(function=None):
    def inner(request, *args, **kwargs):
        user = request.user

        if user.is_authenticated:
            redirect_url = reverse('additional_information')
        else:
            redirect_url = "/login?next={next}".format(next=request.path)

        if user.is_authenticated and user.extended_profile.organization:
            return function(request, *args, **kwargs)
        return HttpResponseRedirect(redirect_to=redirect_url)

    return inner
