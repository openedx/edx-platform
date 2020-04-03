# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView


class MarketplaceListingView(TemplateView):
    template_name = 'features/marketplace/marketplace_listing.html'


class MarketplaceCreateRequestView(TemplateView):
    template_name = 'features/marketplace/markertplace_request_form.html'


class MarketplaceRequestDetailView(TemplateView):
    template_name = 'features/marketplace/marketplace_details.html'
