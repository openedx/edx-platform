"""
API view to allow manipulation of configuration models.
"""
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.serializers import ModelSerializer
from django.db import transaction


class ReadableOnlyByAuthors(DjangoModelPermissions):
    """Only allow access by users with `add` permissions on the model."""
    perms_map = DjangoModelPermissions.perms_map.copy()
    perms_map['GET'] = perms_map['OPTIONS'] = perms_map['HEAD'] = perms_map['POST']


class AtomicMixin(object):
    """Mixin to provide atomic transaction for as_view."""
    @classmethod
    def create_atomic_wrapper(cls, wrapped_func):
        """Returns a wrapped function."""
        def _create_atomic_wrapper(*args, **kwargs):
            """Actual wrapper."""
            # When a view call fails due to a permissions error, it raises an exception.
            # An uncaught exception breaks the DB transaction for any following DB operations
            # unless it's wrapped in a atomic() decorator or context manager.
            with transaction.atomic():
                return wrapped_func(*args, **kwargs)

        return _create_atomic_wrapper

    @classmethod
    def as_view(cls, **initkwargs):
        """Overrides as_view to add atomic transaction."""
        view = super(AtomicMixin, cls).as_view(**initkwargs)
        return cls.create_atomic_wrapper(view)


class ConfigurationModelCurrentAPIView(AtomicMixin, CreateAPIView, RetrieveAPIView):
    """
    This view allows an authenticated user with the appropriate model permissions
    to read and write the current configuration for the specified `model`.

    Like other APIViews, you can use this by using a url pattern similar to the following::

        url(r'config/example_config$', ConfigurationModelCurrentAPIView.as_view(model=ExampleConfig))
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (ReadableOnlyByAuthors,)
    model = None

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self):
        # Return the currently active configuration
        return self.model.current()

    def get_serializer_class(self):
        if self.serializer_class is None:
            class AutoConfigModelSerializer(ModelSerializer):
                """Serializer class for configuration models."""
                class Meta(object):
                    """Meta information for AutoConfigModelSerializer."""
                    model = self.model

            self.serializer_class = AutoConfigModelSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        # Set the requesting user as the one who is updating the configuration
        serializer.save(changed_by=self.request.user)
