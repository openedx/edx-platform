# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views import View
from edxmako.shortcuts import render_to_response


class ChallengeLandingView(View):
    template_name = 'features/idea/challenges_landing.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class IdeaListingView(View):
    template_name = 'features/idea/idea_listing.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class IdeaCreateView(View):
    template_name = 'features/idea/idea_form.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class IdeaDetailView(View):
    template_name = 'features/idea/idea_details.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})
