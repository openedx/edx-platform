# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
from django.views.generic import TemplateView


class IdeaListingView(TemplateView):
    template_name = 'philu/philuapps/idea/templates/idea-listing-template.html'


class IdeaCreateView(TemplateView):
    template_name = 'philu/philuapps/idea/templates/idea-form-template.html'


class IdeaDetailView(TemplateView):
    template_name = 'philu/philuapps/idea/templates/idea-details-template.html'
