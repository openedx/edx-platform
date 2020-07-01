from django.http import JsonResponse
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from .helpers import (
    filter_referred_contacts,
    sort_contacts_by_org_and_user_domain,
    get_platform_contacts_and_non_platform_contacts
)
from .serializers import SmartReferralSerializer
from .tasks import task_send_referral_and_toolkit_emails


class FilterContactsAPIView(APIView):
    """
    FilterContactsAPIView is used to filter user's contacts based on some specific criteria
    """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user_contacts = request.data.get('contacts_list', [])

        # Removing duplicate emails. Same email can present multiple time with different first and last names.
        user_contacts = {contact['contact_email']: contact for contact in user_contacts}.values()

        platform_contacts, non_platform_contacts = get_platform_contacts_and_non_platform_contacts(user_contacts)

        platform_contacts = sort_contacts_by_org_and_user_domain(platform_contacts, user)
        non_platform_contacts = sort_contacts_by_org_and_user_domain(non_platform_contacts, user)

        response = {
            'platform_contacts': platform_contacts,
            'non_platform_contacts': filter_referred_contacts(non_platform_contacts, user),
        }
        return JsonResponse(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthenticationAllowInactiveUser, ])
def send_initial_emails_and_save_record(request):
    serializer = SmartReferralSerializer(context={'request': request}, data=request.data, many=True, allow_empty=False)

    if not serializer.is_valid():
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    smart_referrals = serializer.save()
    contact_emails = [referral.contact_email for referral in smart_referrals]
    task_send_referral_and_toolkit_emails.delay(contact_emails=contact_emails, user_email=request.user.email)
    return Response(status=HTTP_200_OK)
