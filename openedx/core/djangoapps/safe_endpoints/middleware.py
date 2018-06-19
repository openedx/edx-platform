import logging

from rest_framework_jwt.authentication import BaseJSONWebTokenAuthentication


log = logging.getLogger(__name__)


class EnsureJWTAuthSettingsMiddleware(object):
    """
    Django middleware object that ensures the proper Permission classes
    are set on all endpoints that use JWTAuthentication.
    """
    required_permission_classes = ()

    def _includes_base_class(self, iter_classes, base_class):
        """
        Returns whether any class in iter_class is a subclass of the given base_class.
        """
        return any(
            issubclass(auth_class, base_class) for auth_class in iter_classes,
        )

    def process_view(self, request, view_func, view_args, view_kwargs):
        view_class = getattr(view_func, 'view_class', view_func)

        view_authentication_classes = getattr(view_class, 'authentication_classes', tuple())
        if self._includes_base_class(view_authentication_classes, BaseJSONWebTokenAuthentication):

            view_permission_classes = getattr(view_class, 'permission_classes', tuple())

            for perm_class in self.required_permission_classes:

                if not self._includes_base_class(view_permission_classes, perm_class):
                    log.warning(
                        u"The view %s allows Jwt Authentication but needs to include the %s permission class.",
                        view_class.__name__,
                        perm_class.__name__,
                    )

            view_class.permission_classes = view_class.permission_classes or tuple()
            view_class.permission_classes += self.required_permission_classes
