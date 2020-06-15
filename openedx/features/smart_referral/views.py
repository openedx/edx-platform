from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from .serializers import SmartReferralSerializer
from .tasks import task_send_referral_and_toolkit_emails


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
