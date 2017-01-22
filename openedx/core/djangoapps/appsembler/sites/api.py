from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import DefaultStorage
from rest_framework import generics, views, viewsets
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from rest_framework.views import APIView

from .serializers import SiteConfigurationSerializer, SiteConfigurationListSerializer, SiteSerializer,\
    RegistrationSerializer
from .utils import delete_site


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer

    def get_queryset(self):
        queryset = Site.objects.exclude(id=settings.SITE_ID)
        user_email = self.request.query_params.get('user_email')
        if not user_email:
            return Response(status=400)
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(status=400)
        if not user.is_superuser:
            queryset = queryset.filter(organizations=user.organizations.first())
        return queryset


class SiteConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SiteConfiguration.objects.all()
    serializer_class = SiteConfigurationSerializer
    list_serializer_class = SiteConfigurationListSerializer
    create_serializer_class = SiteSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return self.list_serializer_class
        if self.action == 'create':
            return self.create_serializer_class
        return super(SiteConfigurationViewSet, self).get_serializer_class()

    def perform_destroy(self, instance):
        delete_site(instance)


class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):
        file_obj = request.data['file']
        file_path = self.handle_uploaded_file(file_obj, request.GET.get('filename'))
        return Response({'file_path': file_path}, status=201)

    def handle_uploaded_file(self, content, filename):
        storage = DefaultStorage()
        name = storage.save(filename, content)
        return storage.url(name)


class SiteCreateView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer


class UsernameAvailabilityView(APIView):
    def get(self, request, username, format=None):
        try:
            User.objects.get(username=username)
            return Response(None, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)
