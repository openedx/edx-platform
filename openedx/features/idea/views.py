# -*- coding: utf-8 -*-
"""
Views for idea app
"""
from __future__ import unicode_literals

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from edxmako.shortcuts import render_to_response
from openedx.features.user_leads.helpers import save_user_utm

from .forms import IdeaCreationForm
from .models import Idea


class ChallengeLandingView(View):
    """
    Views for Challenge Landing page
    """
    template_name = 'features/idea/challenges_landing.html'

    def get(self, request, *args, **kwargs):
        return render_to_response(self.template_name, {})


class IdeaListingView(ListView):
    """
    Views for Idea Listing page
    """
    model = Idea
    context_object_name = 'idea_list'
    paginate_by = 9
    template_name = 'features/idea/idea_listing.html'
    ordering = ['-created']
    template_engine = 'mako'

    def get_queryset(self):
        queryset = super(IdeaListingView, self).get_queryset()
        save_user_utm(self.request)
        return queryset


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IdeaCreateView(LoginRequiredMixin, CreateView):
    """
    Views for Idea creation page
    """
    form_class = IdeaCreationForm
    template_name = 'features/idea/idea_form.html'
    success_url = reverse_lazy('idea-listing')

    def get_initial(self, *args, **kwargs):  # pylint: disable=unused-argument, arguments-differ
        """Pre-fill form with initial data"""
        initial = super(IdeaCreateView, self).get_initial(**kwargs)
        user = self.request.user
        user_organization = user.extended_profile.organization

        if user_organization:
            initial['organization_name'] = user_organization.label

        initial['country'] = user.profile.country
        initial['city'] = user.profile.city
        initial['user'] = user.profile.user

        return initial


class IdeaDetailView(View):
    """
    Views for Idea detail page
    """
    template_name = 'features/idea/idea_details.html'

    def get(self, request, *args, **kwargs):
        idea = get_object_or_404(Idea, pk=kwargs['pk'])
        context = {'idea': idea}
        return render_to_response(self.template_name, context)
