"""
Views for user sites API
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from lms.djangoapps.mobile_api.decorators import mobile_view
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.features.edly.api.serializers import UserSiteSerializer


@mobile_view()
class UserSitesViewSet(viewsets.ViewSet):
    """
    **Use Case**

        Get information about the current user's sites and mobile configurations
        of the sites with which user is linked.

        Apps hit this endpoint after obtaining access token for a user.

        You can use the **app_configs** value in the response to get a
        mobile configurations for the sites with user is linked.

        You can use the **site_data** value in the response to get a
        branding configurations for the sites with user is linked.

    **Example Request**

        GET /api/mobile/v1/user-sites/

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has the following values.

        * app_config: Mobile configurations for the site which user is linked with.
        * site_data: Branding configurations for the site which user is linked with.
    """
    permission_classes = (IsAuthenticated,)
    serializer = UserSiteSerializer

    def list(self, request, *args, **kwargs):
        user = request.user
        edly_sub_orgs_of_user = user.edly_profile.edly_sub_organizations

        context = {
            'request': request,
        }

        user_sites = []
        for edly_sub_org_of_user in edly_sub_orgs_of_user.all():
            context['edly_sub_org_of_user'] = edly_sub_org_of_user
            site_configuration = SiteConfiguration.get_configuration_for_org(
                edly_sub_org_of_user.get_edx_organizations
            )
            site_configuration = site_configuration.__dict__.get('site_values', {}) if site_configuration else {}
            context['site_configuration'] = site_configuration
            serializer = self.serializer({}, context=context)
            user_sites.append(
                serializer.data
            )

        return Response(user_sites)
