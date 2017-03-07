from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import DefaultStorage
from django.db import transaction
from rest_framework import generics, views, viewsets
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from rest_framework.views import APIView

from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.lib.api.authentication import (
    OAuth2AuthenticationAllowInactiveUser,
)

from tiers.models import Tier
from organizations.models import Organization

from .permissions import AMCAdminPermission
from .serializers import SiteConfigurationSerializer, SiteConfigurationListSerializer, SiteSerializer,\
    RegistrationSerializer
from .utils import delete_site


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
        storage = DefaultStorage()
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


class TierCreateUpdateView(views.APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request):
        params = request.data
        # TODO: Fix this. We should add a unique constraint on the Organiztion model
        # with some field that will be the same in both systems
        org = Organization.objects.filter(name=params['organization_name']).first()
        if org is None:
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        try:
            with transaction.atomic():
                Tier.objects.get(organization=org).delete()
                self._create_tier(org, params)
        except Tier.DoesNotExist:
            self._create_tier(org, params)

        return Response(None, status=status.HTTP_200_OK)

    def _create_tier(self, org, params):
        Tier.objects.create(
            name=params['tier_name'],
            organization=org,
            tier_enforcement_exempt=params['tier_enforcement_exempt'],
            tier_enforcement_grace_period=params['tier_enforcement_grace_period'],
            tier_expires_at=params['tier_expires_at'])

