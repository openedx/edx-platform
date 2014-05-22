""" ORGANIZATIONS API VIEWS """
from rest_framework import viewsets

from api_manager.models import Organization

from .serializers import OrganizationSerializer


class OrganizationsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Organization model.
    """
    serializer_class = OrganizationSerializer
    model = Organization
