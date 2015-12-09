"""
Credentials API views (v1).
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
import json


@login_required()
def generate_program_credential(request):
    user = request.user
    if not user.is_staff:
        return HttpResponseForbidden()

    program_id = request.GET.get('program_id')
    if not program_id:
        return HttpResponseBadRequest()

    usernames = request.GET.get('users')
    if not usernames:
        return HttpResponseBadRequest()

    usernames = usernames.split(',')
    whitelist = request.GET.get('whitelist')
    whitelist_reason = request.GET.get('whitelist_reason')


    data_for_credentials_service = [
        _get_user_context_for_program(username=username, program_id=program_id, whitelist=whitelist,
                                      whitelist_reason=whitelist_reason) for username in usernames if
        User.objects.filter(username=username).exists()
    ]
    # TODO call credential service for generating credentials

    # only for testing purpose
    return HttpResponse(json.dumps(data_for_credentials_service), content_type='application/json')


def _get_user_context_for_program(username, program_id, whitelist=False, whitelist_reason=None):

    # TODO add attributes for white listing
    credential_info = {
        "username": username,
        "program_id": program_id,
        }

    if whitelist:
        credential_info.update({
            "attributes": {
            "namespace": "whitelist", "name": "program_whitelist", "value": whitelist_reason
        }
    })

    return credential_info
