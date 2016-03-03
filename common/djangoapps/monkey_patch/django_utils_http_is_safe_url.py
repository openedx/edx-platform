"""
Monkey patch the is_safe_url method in django.utils.http for Django 1.8.10.
In that release, the method crashes when a bytestring, non-unicode string is passed-in
as the url.
Remove the monkey patch when the bug is fixed in a Django 1.8 release. Here's the bug:
https://code.djangoproject.com/ticket/26308
"""

from django.utils import http
from django.utils.encoding import force_text


def patch():
    """
    Monkey patch the django.utils.http.is_safe_url function to convert the incoming
    url and host parameters to unicode.
    """
    def create_is_safe_url_wrapper(wrapped_func):
        # pylint: disable=missing-docstring
        def _wrap_is_safe_url(*args, **kwargs):
            def _conv_text(value):
                return None if value is None else force_text(value)
            return wrapped_func(
                # Converted *args.
                *tuple(map(_conv_text, args)),
                # Converted **kwargs.
                **{key: _conv_text(value) for key, value in kwargs.items()}
            )
        return _wrap_is_safe_url
    http.is_safe_url = create_is_safe_url_wrapper(http.is_safe_url)
