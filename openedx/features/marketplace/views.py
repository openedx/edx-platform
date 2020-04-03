# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView


class MarketplaceListingView(TemplateView):
    template_name = 'philu/features/templates/marketplace/marketplace-listing-template.html'


class MarketplaceCreateRequestView(TemplateView):
    template_name = 'philu/features/templates/marketplace/markertplace-request-form-template.html'


class MarketplaceRequestDetailView(TemplateView):
    template_name = 'philu/features/templates/marketplace/marketplace-details-template.html'
