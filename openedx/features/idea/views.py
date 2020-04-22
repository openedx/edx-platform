# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views import View
from django.shortcuts import get_object_or_404
from edxmako.shortcuts import render_to_response

from .models import Idea


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
        idea = get_object_or_404(Idea, pk=kwargs['pk'])
        context = {'idea': idea}
        return render_to_response(self.template_name, context)
