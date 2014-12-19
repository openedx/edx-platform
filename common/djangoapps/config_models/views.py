from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.serializers import ModelSerializer


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
    model = None

    def get_queryset(self):
        return self.model.objects.all()

    def get_object(self):
        # Return the currently active configuration
        return self.model.current()

    def get_serializer_class(self):
        if self.serializer_class is None:
            class AutoConfigModelSerializer(ModelSerializer):
                class Meta:
                    model = self.model

            self.serializer_class = AutoConfigModelSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        # Set the requesting user as the one who is updating the configuration
        serializer.save(changed_by = self.request.user)
