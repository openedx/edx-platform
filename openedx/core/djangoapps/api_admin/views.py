"""Views for API management."""
import logging

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from edx_rest_api_client.client import EdxRestApiClient
from edxmako.shortcuts import render_to_response

from openedx.core.djangoapps.api_admin.forms import ApiAccessRequestForm, CatalogForm
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest
from openedx.core.lib.token_utils import get_asymmetric_token

log = logging.getLogger(__name__)


class ApiRequestView(CreateView):
    """Form view for requesting API access."""
    form_class = ApiAccessRequestForm
    template_name = 'api_admin/api_access_request_form.html'
    success_url = reverse_lazy('api_admin:api-status')

    def get(self, request):
        """
        If the requesting user has already requested API access, redirect
        them to the client creation page.
        """
        if ApiAccessRequest.api_access_status(request.user) is not None:
            return redirect(reverse('api_admin:api-status'))
        return super(ApiRequestView, self).get(request)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.site = get_current_site(self.request)
        return super(ApiRequestView, self).form_valid(form)


class ApiRequestStatusView(View):
    """View for confirming our receipt of an API request."""

    def get(self, request):
        """
        If the user has not created an API request, redirect them to the
        request form. Otherwise, display the status of their API request.
        """
        status = ApiAccessRequest.api_access_status(request.user)
        if status is None:
            return redirect(reverse('api_admin:api-request'))
        return render_to_response('api_admin/status.html', {
            'status': status,
            'api_support_link': _('TODO'),
            'api_support_email': settings.API_ACCESS_MANAGER_EMAIL,
        })


class ApiTosView(TemplateView):
    """View to show the API Terms of Service."""

    template_name = 'api_admin/terms_of_service.html'


@never_cache
@staff_member_required
def catalog_changelist(request):
    # TODO: get catalogs
    catalogs = [
        {
            'id': '1',
            'name': 'test1',
            'query': '*'
        }
    ]
    return render(
        RequestContext(request),
        'api_admin/catalog_changelist.html',
        {
            'catalogs': catalogs,
        }
    )


@never_cache
@staff_member_required
def catalog_changeform(request, id=None):
    # import pdb; pdb.set_trace()
    if request.method == 'POST':
        form = CatalogForm(request.POST)
        change = False
        if form.is_valid():
            if id is None:
                log.info("CREATE NEW CATALOGUE")  # create new catalog
            else:
                change = True
                log.info("UPDATE CATALOGUE")  # update catalog
            return HttpResponseRedirect('..')
    else:
        if id is None:  # Create new catalog
            change = False
            form = CatalogForm()
        else:  # Update existing catalog
            change = True
            catalog = {
                'id': '2',
                'name': 'test2',
                'query': 'test*'
            }  # Get catalogs

            form = CatalogForm(catalog)
            # del form.fields['hidden_field']
    return render(
        request,
        'api_admin/catalog_changeform.html',
        {
            'change': change,
            'form': form,
        }
    )


def catalog_client(user):
    token = get_asymmetric_token(user, 'course-discovery')
    return EdxRestApiClient(
        "http://18.111.106.34:8008/api/v1/",
        jwt=token
    )

# from openedx.core.djangoapps.api_admin.views import catalog_client
# from django.contrib.auth.models import User
# user = User.objects.all()[1]
# c = catalog_client(user)
