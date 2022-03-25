import logging
import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, views, viewsets
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import Organization
from tahoe_sites.api import get_organization_user_by_email
from branding.api import get_base_url
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from rest_framework.views import APIView
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.lib.api.authentication import (
    BearerAuthenticationAllowInactiveUser,
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
from openedx.core.djangoapps.appsembler.sites.utils import (
    delete_site,
    get_customer_files_storage,
    to_safe_file_name,
)

log = logging.Logger(__name__)


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    authentication_classes = (BearerAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)

    def get_queryset(self):
        queryset = Site.objects.exclude(id=settings.SITE_ID)
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(organizations__in=user.organizations.all())
        return queryset


class SiteConfigurationViewSet(viewsets.ModelViewSet):
    queryset = SiteConfiguration.objects.all()
    serializer_class = SiteConfigurationSerializer
    list_serializer_class = SiteConfigurationListSerializer
    create_serializer_class = SiteSerializer
    authentication_classes = (BearerAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated, AMCAdminPermission)

    def get_serializer_class(self):
        if self.action == 'list':
            return self.list_serializer_class
        if self.action == 'create':
            return self.create_serializer_class
        return super(SiteConfigurationViewSet, self).get_serializer_class()

    def perform_destroy(self, instance):
        delete_site(instance.site)


class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser,)
    # TODO: oauth token isn't present after step 3 in signup, fix later
    #permission_classes = (AMCAdminPermission,)

    def post(self, request, format=None):
        file_obj = request.data['file']
        file_path = self.handle_uploaded_file(file_obj, request.GET.get('filename'))
        return Response({'file_path': file_path}, status=201)

    def handle_uploaded_file(self, content, filename):
        storage = get_customer_files_storage()
        name = storage.save(filename, content)
        return storage.url(name)


class HostFilesView(views.APIView):
    """
    Host remote static files internally.

    This view hosts files on a Django Storage Backend (e.g. S3 or FileSystem).

    This view is stupid and doesn't try to fix errors, thus it will fail
    if any of the files it will give up and throw an error.

    Usage:

        POST /appsembler/api/host_files
            {
                "urls": [
                    "https://openclipart.org/download/292749/abstract-icon1.png",
                    "https://openclipart.org/download/292749/abstract-icon2.png",
                    "https://openclipart.org/download/292749/abstract-icon3.png",
                ]
            }

        Response on Success:
            Code = 200
            {
                "success": true,
                "urls": [{
                    "source": "https://openclipart.org/download/292749/abstract-icon1.png",
                    "dest": "https://tahoe.appsembler.com/customer_files/c334d1943576/abstract.png"
                }, {
                    "source": "https://openclipart.org/download/292749/abstract-icon2.png",
                    "dest": "https://tahoe.appsembler.com/customer_files/a12bc334fd/abstract.png"
                }, {
                    "source": "https://openclipart.org/download/292749/abstract-icon3.png",
                    "dest": "https://tahoe.appsembler.com/customer_files/c334d1334df/abstract.png"
                }]
            }

        Response on Error:
            Code = 400 or 500
            {
                "success": false,
                "value": "Error processing the provided file",
                "url": "https://openclipart.org/download/292749/abstract-icon3.png"
            }
    """

    parser_classes = (JSONParser,)

    def _logged_response(self, json, status):
        logging.info('Error in processing a file for "HostFilesView", "%s". http_status=%s', json, status)
        return Response(json, status=status)

    def post(self, request):
        storage = get_customer_files_storage()

        urls = request.data.get('urls')

        if not (isinstance(urls, list) and urls):
            return self._logged_response({
                'success': False,
                'value': 'No files were provided.',
            }, status=status.HTTP_400_BAD_REQUEST)

        maximum_files = settings.APPSEMBLER_FEATURES.get('FILE_HOST_MAXIMUM_FILES', 10)
        timeout_secs = settings.APPSEMBLER_FEATURES.get('FILE_HOST_TIMEOUT', 1)
        max_download_size_bytes = settings.APPSEMBLER_FEATURES.get('FILE_HOST_MAX_DOWNLOAD_SIZE', 512 * 1024)

        if len(urls) > maximum_files:
            return self._logged_response({
                'success': False,
                'value': 'Too many files were provided.',
                'maximum_files': maximum_files
            }, status=status.HTTP_400_BAD_REQUEST)

        stored_urls = []

        for source_url in urls:
            try:
                response = requests.get(source_url, timeout=timeout_secs)
            except requests.exceptions.Timeout:
                return self._logged_response({
                    'success': False,
                    'value': 'Request to the needed URL timed out.',
                    'url': source_url,
                    'timeout_seconds': timeout_secs,
                }, status=status.HTTP_400_BAD_REQUEST)
            except requests.exceptions.RequestException:
                return self._logged_response({
                    'success': False,
                    'value': 'Error processing the provided URL.',
                    'url': source_url,
                }, status=status.HTTP_400_BAD_REQUEST)

            if len(response.content) > max_download_size_bytes:
                # TODO: Use a more streamed limit, but probably the timeout would protect against 1TB downloads
                # as most servers can't really download anything over than 12MBytes in a single second
                # But if you're willing see: https://stackoverflow.com/a/23514616/161278
                return self._logged_response({
                    'success': False,
                    'value': 'The file is too large to download.',
                    'url': source_url,
                    'max_size_bytes': max_download_size_bytes,
                }, status=status.HTTP_400_BAD_REQUEST)

            cleaned_up = to_safe_file_name(source_url)
            new_file_name = storage.get_available_name(cleaned_up, max_length=100)

            with storage.open(new_file_name, 'wb') as f:
                f.write(response.content)
                dest_url = get_base_url(request.is_secure()) + storage.url(new_file_name)
                stored_urls.append({
                    'source': source_url,
                    'dest': dest_url,
                })

        return Response({
            'success': True,
            'urls': stored_urls,
        }, status=status.HTTP_200_OK)


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


class FindUsernameByEmailView(APIView):
    """
    View to find username by email to be used in AMC signup workflow.
    """
    permission_classes = [ApiKeyHeaderPermission]

    def get(self, request):
        user_email = request.GET.get('email')
        organization_name = request.GET.get('organization_name')

        if user_email and organization_name:
            try:
                organization = Organization.objects.get(name=organization_name)
                user = get_organization_user_by_email(email=user_email, organization=organization)
                return Response({'username': user.username}, status=status.HTTP_200_OK)
            except ObjectDoesNotExist:
                pass

        return Response({}, status=status.HTTP_404_NOT_FOUND)


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
