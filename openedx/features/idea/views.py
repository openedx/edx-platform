# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import TemplateView


class ChallengeLandingView(TemplateView):
    template_name = 'philu/lms/templates/features/idea/challenges-landing-template.html'


class IdeaListingView(TemplateView):
    template_name = 'philu/lms/templates/features/idea/idea-listing-template.html'


class IdeaCreateView(TemplateView):
    template_name = 'philu/lms/templates/features/idea/idea-form-template.html'


class IdeaDetailView(TemplateView):
    template_name = 'philu/lms/templates/features/idea/idea-details-template.html'
