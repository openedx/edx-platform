# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView


class MarketplaceListingView(TemplateView):
    template_name = 'features/marketplace/marketplace-listing-template.html'


class MarketplaceCreateRequestView(TemplateView):
    template_name = 'features/marketplace/markertplace-request-form-template.html'


class MarketplaceRequestDetailView(TemplateView):
    template_name = 'features/marketplace/marketplace-details-template.html'
