"""
API views for applications app
"""
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework import permissions, viewsets
from rest_framework.authentication import BasicAuthentication

from openedx.core.lib.api.view_utils import view_auth_classes

from .models import Education, WorkExperience
from .serializers import EducationSerializer, WorkExperienceSerializer


@view_auth_classes(is_authenticated=True)
class ApplicationRequirementsViewSetBaseClass(viewsets.ModelViewSet):
    """
    Base class for user application's requirements(Education and Work Experience) apis
    """
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None

    def filter_queryset(self, queryset):
        """
        Filter queryset to allows users to filter only their own objects.
        """
        queryset = queryset.filter(user_application__user=self.request.user)
        return super(ApplicationRequirementsViewSetBaseClass, self).filter_queryset(queryset)


class EducationViewSet(ApplicationRequirementsViewSetBaseClass):
    """
    ViewSet for education apis
    """
    queryset = Education.objects.all()
    serializer_class = EducationSerializer


class WorkExperienceViewSet(ApplicationRequirementsViewSetBaseClass):
    """
    ViewSet for work experience apis
    """
    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer
