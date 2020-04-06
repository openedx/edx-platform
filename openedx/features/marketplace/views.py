# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views import View
from edxmako.shortcuts import render_to_response


class MarketplaceListingView(View):
    template_name = 'features/marketplace/marketplace_listing.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class MarketplaceCreateRequestView(View):
    template_name = 'features/marketplace/markertplace_request_form.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class MarketplaceRequestDetailView(View):
    template_name = 'features/marketplace/marketplace_details.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})
