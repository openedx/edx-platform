"""
All decorators for marketplace
"""
from django.http import HttpResponseRedirect
from django.urls import reverse


def has_affiliated_user(function=None):
    """
    A decorator for user to check its affiliation with organization
    """
    def inner(request, *args, **kwargs):
        """
        Redirect user to login page if user is not logged-in. If user is logged-in but not affiliated to organization
        redirect user to account's additional info page.
        """
        user = request.user

        if user.is_authenticated:
            redirect_url = reverse('additional_information')
        else:
            redirect_url = "/login?next={next}".format(next=request.path)

        if user.is_authenticated and user.extended_profile.organization:
            return function(request, *args, **kwargs)
        return HttpResponseRedirect(redirect_to=redirect_url)

    return inner
