from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from urllib.parse import quote

try:
    from django.utils.functional import empty as _empty
    empty = _empty
except ImportError:  # django < 1.4
    empty = None


from social_core.backends.utils import user_backends_data
from .utils import Storage


class LazyDict(SimpleLazyObject):
    """Lazy dict initialization."""

    def __getitem__(self, name):
        if self._wrapped is empty:
            self._setup()
        return self._wrapped[name]

    def __setitem__(self, name, value):
        if self._wrapped is empty:
            self._setup()
        self._wrapped[name] = value


def backends(request):
    """Load Social Auth current user data to context under the key 'backends'.
    Will return the output of social_core.backends.utils.user_backends_data."""
    return {'backends': LazyDict(lambda: user_backends_data(request.user,
                                                            settings.AUTHENTICATION_BACKENDS,
                                                            Storage))}


def login_redirect(request):
    """Load current redirect to context."""
    value = request.method == 'POST' and \
        request.POST.get(REDIRECT_FIELD_NAME) or \
        request.GET.get(REDIRECT_FIELD_NAME)
    if value:
        value = quote(value)
        querystring = REDIRECT_FIELD_NAME + '=' + value
    else:
        querystring = ''

    return {
        'REDIRECT_FIELD_NAME': REDIRECT_FIELD_NAME,
        'REDIRECT_FIELD_VALUE': value,
        'REDIRECT_QUERYSTRING': querystring
    }
