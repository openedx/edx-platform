from functools import wraps

from django.conf import settings
from django.http import Http404
from django.urls import reverse

from social_core.utils import setting_name, module_member, get_strategy
from social_core.exceptions import MissingBackend


STRATEGY = getattr(settings, setting_name('STRATEGY'),
                   'social_django.strategy.DjangoStrategy')
STORAGE = getattr(settings, setting_name('STORAGE'),
                  'social_django.models.DjangoStorage')
Strategy = module_member(STRATEGY)
Storage = module_member(STORAGE)


def load_strategy(request=None):
    return get_strategy(STRATEGY, STORAGE, request)


def load_backend(strategy, name, redirect_uri):
    return strategy.get_backend(name, redirect_uri=redirect_uri)


def psa(redirect_uri=None, load_strategy=load_strategy):
    def decorator(func):
        @wraps(func)
        def wrapper(request, backend, *args, **kwargs):
            uri = redirect_uri
            if uri and not uri.startswith('/'):
                uri = reverse(redirect_uri, args=(backend,))
            request.social_strategy = load_strategy(request)
            # backward compatibility in attribute name, only if not already
            # defined
            if not hasattr(request, 'strategy'):
                request.strategy = request.social_strategy

            try:
                request.backend = load_backend(request.social_strategy,
                                               backend,
                                               redirect_uri=uri)
            except MissingBackend:
                raise Http404('Backend not found')
            return func(request, backend, *args, **kwargs)
        return wrapper
    return decorator
