"""
OAuth2 provider `django-oauth2-provider` authentication backends
"""

from oauth2_provider.forms import PublicPasswordGrantForm


class PublicPasswordBackend(object):
    """
    Simple client authentication wrapper backends that delegates to
    `oauth2_provider.forms.PublicPasswordGrantForm`
    """

    def authenticate(self, request=None):
        "Returns client if correctly authenticated. Otherwise returns None"
        if request is None:
            return None

        form = PublicPasswordGrantForm(request.REQUEST)

        if form.is_valid():
            return form.cleaned_data.get('client')

        return None
