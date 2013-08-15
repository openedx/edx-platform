"""
Module that tracks analytics events by sending them to different
configurable backends.

The backends can be configured using Django settings as the example
below:


  EVENT_TRACKERS = {
      'name': {
          'ENGINE': 'class.name.for.backend',
          'PARAMETER_ONE': 'VALUE_ONE',
          'PARAMETER_TWO': 'VALUE_TWO',
          ...
      }
  }

"""
import inspect
from importlib import import_module

from django.conf import settings

from track.backends.base import BaseBackend


__all__ = ['send']


_backends = {}


def _initialize_backends_from_django_settings():
    """
    Initialize the event tracking backends according to the
    configuration in django settings
    """
    _backends.clear()

    config = getattr(settings, 'EVENT_TRACKERS', {})

    for name, values in config.iteritems():
        engine = values['ENGINE']
        options = values.get('OPTIONS', {})
        _backends[name] = _instantiate_backend_from_name(engine, options)


def _instantiate_backend_from_name(name, options):
    """
    Instanciate a event tracker backend from the full module path to
    the backend class.
    """
    # Parse backend name

    try:
        parts = name.split('.')
        module_name = '.'.join(parts[:-1])
        class_name = parts[-1]
    except IndexError:
        raise ValueError('Invalid event track backend %s' % name)

    # Get and verify the backend class

    try:
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls) or not issubclass(cls, BaseBackend):
            raise TypeError
    except (ValueError, AttributeError, TypeError, ImportError):
        raise ValueError('Cannot find event track backend %s' % name)

    backend = cls(**options)

    return backend


def send(event):
    for backend in _backends.itervalues():
        backend.send(event)


_initialize_backends_from_django_settings()
