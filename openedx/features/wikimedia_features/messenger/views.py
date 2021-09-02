"""
Views for Messenger
"""
from django.contrib.auth.decorators import login_required

from common.djangoapps.edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user


@login_required
def render_messenger_home(request):
    return render_to_response('messenger.html', {
        'uses_bootstrap': True,
        'login_user_username': request.user.username,
        'login_user_img': get_profile_image_urls_for_user(request.user, request).get("medium")
    })
