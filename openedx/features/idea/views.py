# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views import View
from edxmako.shortcuts import render_to_response
from django.views.generic.list import ListView

from .models import Idea


class ChallengeLandingView(View):
    template_name = 'features/idea/challenges_landing.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class IdeaListingView(ListView):
    model = Idea
    context_object_name = 'idea_list'
    paginate_by = 9
    template_name = 'features/idea/idea_listing.html'
    ordering = ['-created']
    template_engine = 'mako'


class IdeaCreateView(View):
    template_name = 'features/idea/idea_form.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class IdeaDetailView(View):
    template_name = 'features/idea/idea_details.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})
