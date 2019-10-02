import json

from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from rest_framework import status

email_template = '''
    Course : {course}
    Name: {name}
    Email : {email}

    {body}
    '''


@require_http_methods(["POST"])
def email_support(request):
    """
    A View that will send user support (contact-form) emails to a specific
    account.
    """

    body = json.loads(request.body)
    subject = body['subject']

    data = {
        'name': body['requester']['name'],
        'email': body['requester']['email'],
        'body': body['comment']['body'],
        'course': body['custom_fields'][0]['value']
    }

    content = email_template.format(**data)
    response = send_mail(subject, content, settings.DEFAULT_FROM_EMAIL,
                         settings.SUPPORT_DESK_EMAILS, fail_silently=False)

    if response:
        return HttpResponse(status=status.HTTP_201_CREATED)
    else:
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)