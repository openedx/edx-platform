"""
Support tool for disabling user accounts.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from rest_framework.generics import GenericAPIView

from edxmako.shortcuts import render_to_response
from lms.djangoapps.support.decorators import require_support_permission
from openedx.core.djangoapps.user_api.accounts.serializers import AccountUserSerializer
from openedx.core.djangoapps.user_api.accounts.utils import generate_password
from util.json_request import JsonResponse


class ManageUserSupportView(View):
    """
    View for viewing and managing user accounts, used by the
    support team.
    """

    @method_decorator(require_support_permission)
    def get(self, request):
        """Render the manage user support tool view."""
        return render_to_response('support/manage_user.html', {
            _('username'): request.GET.get('user', ''),
            _('user_support_url'): reverse('support:manage_user'),
            _('user_detail_url'): reverse('support:manage_user_detail')
        })


class ManageUserDetailView(GenericAPIView):
    """
    Allows viewing and disabling learner accounts by support
    staff.
    """
    # TODO: ARCH-91
    # This view is excluded from Swagger doc generation because it
    # does not specify a serializer class.
    exclude_from_schema = True

    @method_decorator(require_support_permission)
    def get(self, request, username_or_email):
        """
        Returns details for the given user, along with
        information about its username and joining date.
        """
        try:
            user = get_user_model().objects.get(
                Q(username=username_or_email) | Q(email=username_or_email)
            )
            data = AccountUserSerializer(user, context={'request': request}).data
            data['status'] = _('Usable') if user.has_usable_password() else _('Unusable')
            return JsonResponse(data)
        except get_user_model().DoesNotExist:
            return JsonResponse([])

    @method_decorator(require_support_permission)
    def post(self, request, username_or_email):
        """Allows support staff to disable a user's account."""
        user = get_user_model().objects.get(
            Q(username=username_or_email) | Q(email=username_or_email)
        )
        if user.has_usable_password():
            user.set_unusable_password()
        else:
            user.set_password(generate_password(length=25))
        user.save()

        if user.has_usable_password():
            password_status = _('Usable')
            msg = _('User Enabled Successfully')
        else:
            password_status = _('Unusable')
            msg = _('User Disabled Successfully')
        return JsonResponse({'success_msg': msg, 'status': password_status})
