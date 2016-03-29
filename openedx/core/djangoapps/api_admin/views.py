"""Views for API management."""
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.edit import CreateView

from edxmako.shortcuts import render_to_response, render_to_string
from openedx.core.djangoapps.api_admin.forms import ApiAccessRequestForm
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest

log = logging.getLogger(__name__)


class ApiRequestView(CreateView):
    """Form view for requesting API access."""
    form_class = ApiAccessRequestForm
    template_name = 'api_admin/api_access_request_form.html'
    success_url = reverse_lazy('api-status')

    def get(self, request):
        """
        If the requesting user has already requested API access, redirect
        them to the client creation page.
        """
        if ApiAccessRequest.api_access_status(request.user) is not None:
            return redirect(reverse('api-status'))
        return super(ApiRequestView, self).get(request)

    def send_email(self, api_request):
        """
        Send an email to settings.API_ACCESS_MANAGER_EMAIL with the
        contents of this API access request.
        """
        context = {
            'approval_url': self.request.build_absolute_uri(
                reverse('admin:api_admin_apiaccessrequest_change', args=(api_request.id,))
            ),
            'company_name': api_request.company_name,
            'username': api_request.user.username,
            'url': api_request.website,
            'company_address': api_request.company_address,
            'reason': api_request.reason,
        }
        message = render_to_string('api_admin/email.txt', context)
        try:
            send_mail(
                _('API access request from {company}').format(company=api_request.company_name),
                message,
                settings.API_ACCESS_FROM_EMAIL,
                [settings.API_ACCESS_MANAGER_EMAIL],
                fail_silently=False
            )
        except SMTPException:
            log.exception('Error sending API request email for request [%s].', api_request.id)

    def form_valid(self, form):
        form.instance.user = self.request.user
        result = super(ApiRequestView, self).form_valid(form)
        self.send_email(form.instance)
        return result


class ApiRequestStatusView(View):
    """View for confirming our receipt of an API request."""

    def get(self, request):
        """
        If the user has not created an API request, redirect them to the
        request form. Otherwise, display the status of their API request.
        """
        status = ApiAccessRequest.api_access_status(request.user)
        if status is None:
            return redirect(reverse('api-request'))
        return render_to_response('api_admin/status.html', {
            'status': status,
            'api_support_link': _('TODO'),
            'api_support_email': settings.API_ACCESS_MANAGER_EMAIL,
        })
