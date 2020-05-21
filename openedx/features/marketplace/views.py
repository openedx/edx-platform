# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View, generic

from edxmako.shortcuts import render_to_response
from openedx.features.marketplace.decorators import has_affiliated_user
from openedx.features.marketplace.forms import MarketplaceRequestForm
from openedx.features.user_leads.helpers import save_user_utm

from .models import MarketplaceRequest


class MarketplaceListingView(View):
    template_name = 'features/marketplace/marketplace_listing.html'

    def get(self, request, *args, **kwargs):
        save_user_utm(request)
        return render_to_response(self.template_name, {})


@method_decorator(has_affiliated_user, name='dispatch')
class MarketplaceCreateRequestView(generic.CreateView, LoginRequiredMixin):
    form_class = MarketplaceRequestForm
    template_name = 'features/marketplace/markertplace_request_form.html'

    def get_success_url(self):
        return reverse('marketplace-listing')

    def get_initial(self, *args, **kwargs):
        initial = super(MarketplaceCreateRequestView, self).get_initial(**kwargs)
        user = self.request.user
        initial['user'] = user
        initial['organization'] = user.extended_profile.organization
        return initial


class MarketplaceRequestDetailView(View):
    template_name = 'features/marketplace/marketplace_details.html'

    def get(self, request, *args, **kwargs):
        marketplace_request = get_object_or_404(MarketplaceRequest, pk=kwargs['pk'])
        context = {'marketplace_request': marketplace_request}
        return render_to_response(self.template_name, context)
