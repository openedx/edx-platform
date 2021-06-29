"""
API views for applications app
"""
import json

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from openedx.adg.lms.applications.models import Education, Reference, WorkExperience
from openedx.core.lib.api.view_utils import view_auth_classes

from .serializers import EducationSerializer, ReferenceSerializer, WorkExperienceSerializer


@view_auth_classes(is_authenticated=True)
class ApplicationRequirementsViewSet(viewsets.ModelViewSet):
    """
    Base class for user application's requirements(Education and Work Experience) apis
    """

    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    http_method_names = ['get', 'post', 'head', 'put', 'patch', 'delete']

    def filter_queryset(self, queryset):
        """
        Filter queryset to allow users to filter only their own objects.
        """
        queryset = queryset.filter(user_application__user=self.request.user)
        return super(ApplicationRequirementsViewSet, self).filter_queryset(queryset)


class EducationViewSet(ApplicationRequirementsViewSet):
    """
    ViewSet for education apis

    retrieve:
        Return a single education record that matches requested id.

    **Example Requests**
    GET /api/applications/education/{id}/

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
    DELETE /api/applications/education/{id}/

    update:
        Update an existing education record.

    **Example Requests**
    PUT /api/applications/education/{id}/
    """

    queryset = Education.objects.all()
    serializer_class = EducationSerializer


class WorkExperienceViewSet(ApplicationRequirementsViewSet):
    """
    ViewSet for work experience apis

    retrieve:
        Return a single work experience record that matches requested id.

    **Example Requests**
    GET /api/applications/work_experience/{id}/

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
    DELETE /api/applications/work_experience/{id}/

    update:
        Update an existing work experience record.

    **Example Requests**
    PUT /api/applications/work_experience/{id}/

    partial_update:
        Update user work_experience is not applicable

    **Example Requests**
    PATCH /api/applications/work_experience/update_is_not_applicable/
    """

    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer

    @action(detail=False, methods=['patch'], url_name='update_is_not_applicable', url_path='update_is_not_applicable')
    def update_is_work_experience_not_applicable(self, request):
        """
        Update is_work_experience_not_applicable to True or False and delete all existing work experience records
        if update to True.
        """
        is_work_experience_not_applicable = json.loads(request.data.get('is_work_experience_not_applicable', 'false'))
        user_application = request.user.application
        user_application.is_work_experience_not_applicable = is_work_experience_not_applicable
        with transaction.atomic():
            user_application.save()
            if is_work_experience_not_applicable:
                user_application.applications_workexperiences.all().delete()

        return Response({}, status=HTTP_200_OK)


class ReferenceViewSet(ApplicationRequirementsViewSet):
    """
    ViewSet for reference APIs

    retrieve:
        Return a single reference record that matches requested id.

    **Example Requests**
    GET /api/applications/reference/{id}/

    list:
        Return all reference records belong to the requested user.

    **Example Requests**
    GET /api/applications/reference/

    create:
        Create a new reference record.

    Following points must be kept in mind when creating a new reference record:

    * Id field is read only and would have no effect if provided explicitly.

    **Example Requests**
    POST /api/applications/reference/

    delete:
        Remove an existing reference record.

    **Example Requests**
    DELETE /api/applications/reference/{id}/

    update:
        Update an existing reference record.

    **Example Requests**
    PUT /api/applications/reference/{id}/
    """

    queryset = Reference.objects.all()
    serializer_class = ReferenceSerializer
