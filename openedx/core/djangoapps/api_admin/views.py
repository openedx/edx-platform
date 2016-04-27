"""Views for API management."""
import logging
from urlparse import urljoin

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse_lazy, reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from edxmako.shortcuts import render_to_response

from openedx.core.djangoapps.api_admin.forms import ApiAccessRequestForm, CatalogForm
from openedx.core.djangoapps.api_admin.models import ApiAccessRequest, Catalog

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


class CatalogSearchView(View):
    """View to search for catalogs belong to a user."""

    def get(self, request):
        return render_to_response('api_admin/catalogs/search.html')

    def post(self, request):
        username = request.POST.get('username')
        # If no username is provided, bounce back to this page.
        if not username:
            return redirect(reverse('api_admin:catalog-search'))
        return redirect(reverse('api_admin:catalog-list', kwargs={'username': username}))


class CatalogListView(View):
    """View to list existing catalogs and create new ones."""

    template = 'api_admin/catalogs/list.html'

    def get(self, request, username):
        """Display a list of a user's catalogs."""
        # TODO actually get these catalogs, and filter by user
        return render_to_response(self.template, {
            'username': username,
            'catalogs': Catalog.all(),
            'form': CatalogForm(initial={'username': username}),
        })

    def post(self, request, username):
        """Create a new catalog for a user."""
        form = CatalogForm(request.POST)
        if not form.is_valid():
            return render_to_response(self.template, {
                'form': form,
                'catalogs': Catalog.all(),
                'username': username,
            })
        form.save()
        # return redirect(reverse('api_admin:catalog-detail', kwargs={'catalog_id': form.instance.id}))
        # TODO: redirect to the correct catalog. right now we don't have an ID.
        return redirect(reverse('api_admin:catalog-detail', kwargs={'catalog_id': '1'}))


class CatalogDetailView(View):
    """View to show an individual catalog."""

    def get(self, request, catalog_id):
        """Display this catalog."""
        catalog = Catalog.all()[int(catalog_id)]  # TODO: actually get this catalog
        return render_to_response('api_admin/catalogs/detail.html', {
            'catalog': catalog,
            'edit_link': reverse('api_admin:catalog-edit', kwargs={'catalog_id': catalog_id}),
            'preview_link': urljoin(  # TODO: link to a preview in CD
                settings.COURSE_DISCOVERY_API_URL, 'catalogs/{id}/courses'.format(id=catalog_id)
            ),
        })


class CatalogEditView(View):
    """View to edit an individual catalog."""

    def get(self, request, catalog_id):
        """Display a form to edit this catalog"""
        catalog = Catalog.all()[int(catalog_id)]  # TODO: actually get this catalog
        form = CatalogForm(instance=catalog)
        return render_to_response('api_admin/catalogs/edit.html', {
            'catalog': catalog,
            'form': form,
        })

    def post(self, request, catalog_id):
        """Update or delete this catalog."""
        if request.POST.get('delete-catalog') == 'on':
            # TODO delete catalog
            return redirect(reverse('api_admin:catalog-list', kwargs={'username': 'TODO'}))  # TODO redirect correctly
        form = CatalogForm(request.POST)
        if not form.is_valid():
            catalog = Catalog.all()[int(catalog_id)]  # TODO: actually get this catalog
            return render_to_response('api_admin/catalogs/edit.html', {
                'catalog': catalog,
                'form': form,
            })
        form.save()
        return redirect(reverse('api_admin:catalog-detail', kwargs={'catalog_id': catalog_id}))
