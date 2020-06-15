from django.http import JsonResponse
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .helpers import sort_contacts_by_org_and_user_domain, get_platform_contacts_and_non_platform_contacts


class FilterContactsAPIView(APIView):
    """
    FilterContactsAPIView is used to filter user's contacts based on some specific criteria
    """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_contacts = request.data.get('contacts_list', '')

        platform_contacts, non_platform_contacts = get_platform_contacts_and_non_platform_contacts(user_contacts)

        platform_contacts = sort_contacts_by_org_and_user_domain(platform_contacts, user)
        non_platform_contacts = sort_contacts_by_org_and_user_domain(non_platform_contacts, user)

        response = {
            'message': 'Success',
            'platform_contacts': platform_contacts,
            'non_platform_contacts': non_platform_contacts,
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
