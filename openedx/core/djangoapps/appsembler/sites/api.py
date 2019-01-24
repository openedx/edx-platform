from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import DefaultStorage, get_storage_class
from rest_framework import generics, views, viewsets
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from rest_framework.views import APIView

from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)

from openedx.core.djangoapps.appsembler.sites.models import AlternativeDomain
from openedx.core.djangoapps.appsembler.sites.permissions import AMCAdminPermission
from openedx.core.djangoapps.appsembler.sites.serializers import (
    SiteConfigurationSerializer,
    SiteConfigurationListSerializer,
    SiteSerializer,
    RegistrationSerializer,
    AlternativeDomainSerializer,
)
from openedx.core.djangoapps.appsembler.sites.utils import delete_site


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)

    def get_queryset(self):
        queryset = Site.objects.exclude(id=settings.SITE_ID)
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(organizations=user.organizations.all())
        return queryset


class SiteConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SiteConfiguration.objects.all()
    serializer_class = SiteConfigurationSerializer
    list_serializer_class = SiteConfigurationListSerializer
    create_serializer_class = SiteSerializer
    authentication_classes = (OAuth2AuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)

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
    # TODO: oauth token isn't present after step 3 in signup, fix later
    #permission_classes = (AMCAdminPermission,)

    def post(self, request, format=None):
        file_obj = request.data['file']
        file_path = self.handle_uploaded_file(file_obj, request.GET.get('filename'))
        return Response({'file_path': file_path}, status=201)

    def handle_uploaded_file(self, content, filename):
        kwargs = {}
        # passing these settings to the FileSystemStorage causes an exception
        if not settings.DEBUG:
            kwargs = {
                'location': "customer_files",
                'file_overwrite': False
            }
        storage = get_storage_class()(**kwargs)
        name = storage.save(filename, content)
        return storage.url(name)


class SiteCreateView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = (ApiKeyHeaderPermission,)


class UsernameAvailabilityView(APIView):
    def get(self, request, username, format=None):
        try:
            User.objects.get(username=username)
            return Response(None, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)


class DomainAvailabilityView(APIView):
    def get(self, request, subdomain, format=None):
        try:
            Site.objects.get(name=subdomain)
            return Response(None, status=status.HTTP_200_OK)
        except Site.DoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)


class DomainSwitchView(APIView):
    def post(self, request, format=None):
        site_id = request.data.get('site')
        if not site_id:
            return Response("Site ID needed", status=status.HTTP_400_BAD_REQUEST)
        try:
            site = Site.objects.get(id=site_id)
            if not site.alternative_domain:
                return Response("Site {} does not have a custom domain".format(site.domain),
                                status=status.HTTP_404_NOT_FOUND)
            site.alternative_domain.switch_with_active()
            return Response(status=status.HTTP_200_OK)
        except Site.DoesNotExist:
            return Response("The site with ID {} does not exist".format(site_id),
                            status=status.HTTP_404_NOT_FOUND)


class CustomDomainView(CreateAPIView):
    queryset = AlternativeDomain.objects.all()
    serializer_class = AlternativeDomainSerializer
