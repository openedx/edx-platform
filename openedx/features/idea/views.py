# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView


class ChallengeLandingView(TemplateView):
    template_name = 'features/idea/challenges_landing.html'


class IdeaListingView(TemplateView):
    template_name = 'features/idea/idea_listing.html'


class IdeaCreateView(TemplateView):
    template_name = 'features/idea/idea_form.html'


class IdeaDetailView(TemplateView):
    template_name = 'features/idea/idea_details.html'
