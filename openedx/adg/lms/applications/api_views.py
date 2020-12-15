"""
API views for applications app
"""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

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
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']

    def filter_queryset(self, queryset):
        """
        Filter queryset to allows users to filter only their own objects.
        """
        queryset = queryset.filter(user_application__user=self.request.user)
        return super(ApplicationRequirementsViewSetBaseClass, self).filter_queryset(queryset)


class EducationViewSet(ApplicationRequirementsViewSetBaseClass):
    """
    ViewSet for education apis

    retrieve:
        Return a single education record that matches requested id.

    **Example Requests**
    GET /api/applications/education/

    list:
        Return all education records belong to the requested user.

    **Example Requests**
    GET /api/applications/education/

    create:
        Create a new education record.

    Following points must be kept in mind when creating a new education record:

    * Id, created and modified fields are readable and would have no effect if provided explicitly.
    * Area of study is required for all degrees except for high school diploma(HD).
    * Date completed month and date completed year must only be provided for past degrees.
    * If 'is_in_progress' isn't provided, it's value will be consider as 'False'.

    **Example Requests**
    POST /api/applications/education/

    delete:
        Remove an existing education record.

    **Example Requests**
    DELETE /api/applications/education/

    partial_update:
        Update an existing education record.

    **Example Requests**
    PATCH /api/applications/education/

    """
    queryset = Education.objects.all()
    serializer_class = EducationSerializer


class WorkExperienceViewSet(ApplicationRequirementsViewSetBaseClass):
    """
    ViewSet for work experience apis

    retrieve:
        Return a single work experience record that matches requested id.

    **Example Requests**
    GET /api/applications/work_experience/

    list:
        Return all work experience records belong to the requested user.

    **Example Requests**
    GET /api/applications/work_experience/

    create:
        Create a new work experience record.

    Following points must be kept in mind when creating a new work experience record:

    * Id, created and modified fields are readable and would have no effect if provided explicitly.
    * Date completed month and date completed year must only be provided for past work experiences.
    * If 'is_current_position' isn't provided, it's value will be consider as 'False'.

    **Example Requests**
    POST /api/applications/work_experience/

    delete:
        Remove an existing work experience record.

    **Example Requests**
    DELETE /api/applications/work_experience/

    partial_update:
        Update an existing work experience record.

    **Example Requests**
    PATCH /api/applications/work_experience/

    """
    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer
