# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
from django.views.generic import TemplateView


class MarketplaceListingView(TemplateView):
    template_name = 'philu/philuapps/marketplace/templates/marketplace-listing-template.html'


class MarketplaceCreateRequestView(TemplateView):
    template_name = 'philu/philuapps/marketplace/templates/markertplace-request-form-template.html'


class MarketplaceRequestDetailView(TemplateView):
    template_name = 'philu/philuapps/marketplace/templates/marketplace-details-template.html'
