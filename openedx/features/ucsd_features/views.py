import json
from django.conf import settings
from rest_framework import status
from django.http import HttpResponse
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from openedx.features.ucsd_features.utils import send_notification_email_to_support


@require_http_methods(["POST"])
def email_support(request):
    """
    A View that will send user support (contact-form) emails to a specific
    account.
    """
    body = json.loads(request.body)

    response = send_notification_email_to_support(
        subject=body['subject'],
        body=body['comment']['body'],
        name=body['requester']['name'],
        email=body['requester']['email'],
        course=body['custom_fields'][0]['value']
    )
    if response:
        return HttpResponse(status=status.HTTP_201_CREATED)
    else:
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
