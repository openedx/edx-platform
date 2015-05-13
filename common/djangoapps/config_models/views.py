from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.authentication import SessionAuthentication


class ReadableOnlyByAuthors(DjangoModelPermissions):
    perms_map = DjangoModelPermissions.perms_map.copy()
    perms_map['GET'] = perms_map['OPTIONS'] = perms_map['HEAD'] = perms_map['POST']


class ConfigurationModelCurrentAPIView(CreateAPIView, RetrieveAPIView):
    """
    This view allows an authenticated user with the appropriate model permissions
    to read and write the current configuration for the specified `model`.

    Like other APIViews, you can use this by using a url pattern similar to the following::

        url(r'config/example_config$', ConfigurationModelCurrentAPIView.as_view(model=ExampleConfig))
    """
    authentication_classes = (SessionAuthentication,)
    permission_classes = (ReadableOnlyByAuthors,)

    def get_object(self):
        # Return the currently active configuration
        return self.model.current()

    def pre_save(self, object):
        # Set the requesting user as the one who is updating the configuration
        object.changed_by = self.request.user
