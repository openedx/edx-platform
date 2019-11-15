from rest_framework import mixins

from organizations.v0.views import OrganizationsViewSet


class PlatformOrganizationsViewSet(mixins.CreateModelMixin,
                                   mixins.UpdateModelMixin,
                                   OrganizationsViewSet):
    """
    We take the ViewSet from the edx-organizations repo which is read-only,
    and extend it here to allow creation and updating.  The current purpose of
    this is to allow pushing of organization data from course-discovery to platform.
    """
    pass
