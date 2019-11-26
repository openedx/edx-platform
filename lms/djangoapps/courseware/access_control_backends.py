"""
A plugin system for customizing access control in the platform.
"""
from importlib import import_module
from lazy import lazy
import logging
import six

from django.conf import settings

log = logging.getLogger(__name__)


class AccessControlBackends(object):
    """
    The access control backend service object.

    Meant to be instantiated by this module, so use the `access_control_backends` object.
    """
    SUPPORTED_ACTIONS = {
        'course.load',
        'course.load_mobile',
        'course.enroll',
        'course.see_exists',
        'course.staff',
        'course.instructor',
        'course.see_in_catalog',
        'course.see_about_page',
    }
    UNSUPPORTED_ERROR_FMT = '`AccessControlBackends` does not support the action `{action}` yet'.format

    @lazy
    def backends(self):
        """
        Parse the access control backends settings and resolve the backend functions.

        :return: a dictionary with the following format: {
            ACTION_NAME: {
                "FUNC": BACKEND_FUNCTION,
                "OPTIONS": BACKEND_OPTIONS_DICT,
            },
            ANOTHER_ACTION_NAME: ...,
        }
        """
        backends = settings.ACCESS_CONTROL_BACKENDS
        resolved_backends = {}
        for action, backend in six.iteritems(backends):
            if action not in self.SUPPORTED_ACTIONS:
                raise NotImplementedError(self.UNSUPPORTED_ERROR_FMT(action=action))

            path = backend['NAME']
            options = backend.get('OPTIONS', {})
            try:
                module, func_name = path.split(':', 1)
                module = import_module(module)
                func = getattr(module, func_name)
                resolved_backends[action] = {
                    'FUNC': func,
                    'OPTIONS': options,
                }
            except Exception:
                log.exception(
                    'Something went wrong in reading the ACCESS_CONTROL_BACKENDS settings for `{action}`.'.format(
                        action=action,
                    )
                )
                raise

        return resolved_backends

    def query(self, action, user, resource, default_has_access):
        """
        Invoke an Access Control Backend.

        :param action: currently supporting the course access actions in SUPPORTED_ACTIONS.
        :param user: The User model object.
        :param resource: The course/resource ID.
        :param default_has_access: AccessResponse The default access response object by Open edX.
        :return: AccessResponse: ACCESS_GRANTED or ACCESS_DENIED whether the
                                 `user` can perform the `action` on the `resource` or not.
        """
        if action not in self.SUPPORTED_ACTIONS:
            raise NotImplementedError(self.UNSUPPORTED_ERROR_FMT(action=action))

        backend = self.backends.get(action)

        if backend:
            try:
                backend_func = backend['FUNC']
                return backend_func(
                    user=user,
                    resource=resource,
                    default_has_access=default_has_access,
                    options=backend['OPTIONS'],
                )
            except Exception:
                log.exception(
                    'Something went wrong in querying the access control backend for `{action}`.'.format(
                        action=action,
                    )
                )
                raise

        return default_has_access


access_control_backends = AccessControlBackends()
