# -*- coding: utf-8 -*-
"""
All views for marketplace
"""
from __future__ import unicode_literals

import operator

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django_countries import countries

from openedx.features.marketplace.decorators import has_affiliated_user
from openedx.features.marketplace.forms import MarketplaceRequestForm
from openedx.features.user_leads.helpers import save_user_utm

from .constants import (
    DJANGO_COUNTRIES_INDEX,
    DJANGO_COUNTRIES_VALUE_INDEX,
    MARKETPLACE_PARAM_CITY,
    MARKETPLACE_PARAM_COUNTRY,
    MARKETPLACE_PARAM_QUERY,
    ORG_PROBLEM_TEMPLATE_CHOICES,
    ORG_PROBLEM_TYPE_DELIVERY_SERVICES,
    ORG_PROBLEM_TYPE_FUNDING,
    ORG_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES,
    ORG_PROBLEM_TYPE_HUMAN_RESOURCES,
    ORG_PROBLEM_TYPE_MENTORSHIP,
    ORG_PROBLEM_TYPE_ONLINE_TRAINING,
    ORG_PROBLEM_TYPE_OTHER,
    ORG_PROBLEM_TYPE_REMOTE_WORKING_TOOLS,
    ORG_SECTOR_ART_AND_CULTURE,
    ORG_SECTOR_CLEAN_ENERGY,
    ORG_SECTOR_CLIMATE_CHANGES,
    ORG_SECTOR_EDUCATION,
    ORG_SECTOR_ENVIRONMENTAL_CONSERVATION,
    ORG_SECTOR_GENDER_EQUALITY,
    ORG_SECTOR_HEALTH_AND_WELL_BEING,
    ORG_SECTOR_HUMAN_RIGHTS,
    ORG_SECTOR_OTHER,
    ORG_SECTOR_SANITATION,
    ORG_SECTOR_SOCIAL_JUSTICE,
    ORG_SECTOR_TEMPLATE_CHOICES,
    ORG_SECTOR_WORK_AND_ECONOMIC_GROWTH
)
from .models import MarketplaceRequest


class MarketplaceListView(ListView):
    """
    View for marketplace listing
    """
    model = MarketplaceRequest
    context_object_name = 'marketplace_requests'
    paginate_by = 10
    template_name = 'features/marketplace/marketplace_listing.html'
    ordering = ['-created']
    template_engine = 'mako'

    def get_checked_choices(self, choices):
        """
        This method takes list of tuples (choices) and returns a list
        of choice keys that exist in self.request.GET
        :param: choices
        :return: list of choice keys that are also in self.request.GET
        """
        params = self.request.GET
        choice_key_index = 0
        return [choice[choice_key_index] for choice in choices if params.get(choice[choice_key_index])]

    def get_queryset(self):
        params = self.request.GET

        query = params.get(MARKETPLACE_PARAM_QUERY)
        city = params.get(MARKETPLACE_PARAM_CITY)
        country = params.get(MARKETPLACE_PARAM_COUNTRY)

        organizational_request_type_list = self.get_checked_choices(ORG_PROBLEM_TEMPLATE_CHOICES)
        organizational_sector_list = self.get_checked_choices(ORG_SECTOR_TEMPLATE_CHOICES)
        marketplace_list_queryset = super(MarketplaceListView, self).get_queryset()

        if organizational_request_type_list:
            # has other problem selected
            if ORG_PROBLEM_TYPE_OTHER in organizational_request_type_list:
                marketplace_list_queryset = marketplace_list_queryset.filter(
                    reduce(operator.or_, (~Q(organizational_problems__endswith='|')
                                          | Q(organizational_problems__contains=request_type)
                                          for request_type in organizational_request_type_list)))
            else:
                marketplace_list_queryset = marketplace_list_queryset.filter(
                    reduce(operator.or_, (Q(organizational_problems__contains=request_type)
                                          for request_type in organizational_request_type_list)))
        if organizational_sector_list:
            # has other sector selected
            if ORG_SECTOR_OTHER in organizational_sector_list:
                marketplace_list_queryset = marketplace_list_queryset.filter(
                    reduce(operator.or_, (~Q(organization_sector__endswith='|')
                                          | Q(organization_sector__contains=sector)
                                          for sector in organizational_sector_list)))
            else:
                marketplace_list_queryset = marketplace_list_queryset.filter(
                    reduce(operator.or_, (Q(organization_sector__contains=sector)
                                          for sector in organizational_sector_list)))

        if country:
            country_codes = [django_country[DJANGO_COUNTRIES_INDEX] for django_country in countries if
                             country.lower() in django_country[DJANGO_COUNTRIES_VALUE_INDEX].lower()]
            marketplace_list_queryset = marketplace_list_queryset.filter(country__in=country_codes)
        if city:
            marketplace_list_queryset = marketplace_list_queryset.filter(city__icontains=city)
        if query:
            marketplace_list_queryset = marketplace_list_queryset.filter(
                Q(organization_mission__icontains=query) | Q(organization__label__icontains=query))

        # Saving UTM Params
        save_user_utm(self.request)
        return marketplace_list_queryset

    def get_context_data(self, **kwargs):
        context = super(MarketplaceListView, self).get_context_data(**kwargs)
        params = self.request.GET

        context['search_fields'] = {
            'query': params.get(MARKETPLACE_PARAM_QUERY),
            'city': params.get(MARKETPLACE_PARAM_CITY),
            'country': params.get(MARKETPLACE_PARAM_COUNTRY),
            'delivery-services': params.get(ORG_PROBLEM_TYPE_DELIVERY_SERVICES),
            'funding': params.get(ORG_PROBLEM_TYPE_FUNDING),
            'healthcare-supplies': params.get(ORG_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES),
            'human-resources': params.get(ORG_PROBLEM_TYPE_HUMAN_RESOURCES),
            'mentorship': params.get(ORG_PROBLEM_TYPE_MENTORSHIP),
            'online-training': params.get(ORG_PROBLEM_TYPE_ONLINE_TRAINING),
            'remote-working-tools': params.get(ORG_PROBLEM_TYPE_REMOTE_WORKING_TOOLS),
            'health-and-well-being': params.get(ORG_SECTOR_HEALTH_AND_WELL_BEING),
            'education': params.get(ORG_SECTOR_EDUCATION),
            'gender-equality': params.get(ORG_SECTOR_GENDER_EQUALITY),
            'sanitation': params.get(ORG_SECTOR_SANITATION),
            'climate-changes': params.get(ORG_SECTOR_CLIMATE_CHANGES),
            'clean-energy': params.get(ORG_SECTOR_CLEAN_ENERGY),
            'environmental-conservation': params.get(ORG_SECTOR_ENVIRONMENTAL_CONSERVATION),
            'work-and-economic-growth': params.get(ORG_SECTOR_WORK_AND_ECONOMIC_GROWTH),
            'human-rights': params.get(ORG_SECTOR_HUMAN_RIGHTS),
            'social-justice': params.get(ORG_SECTOR_SOCIAL_JUSTICE),
            'art-and-culture': params.get(ORG_SECTOR_ART_AND_CULTURE),
            'other-sector': params.get(ORG_SECTOR_OTHER),
            'other-problem': params.get(ORG_PROBLEM_TYPE_OTHER),
        }

        context['filtered'] = any(context['search_fields'].values())

        return context


@method_decorator(has_affiliated_user, name='dispatch')
class MarketplaceCreateRequestView(generic.CreateView, LoginRequiredMixin):
    """
    Marketplace view to post a request to the community hub
    """
    form_class = MarketplaceRequestForm
    template_name = 'features/marketplace/markertplace_request_form.html'

    def get_success_url(self):
        return reverse('marketplace-listing')

    def get_initial(self, *args, **kwargs):  # pylint: disable=arguments-differ, unused-argument
        initial = super(MarketplaceCreateRequestView, self).get_initial(**kwargs)
        user = self.request.user
        initial['user'] = user
        initial['organization'] = user.extended_profile.organization
        return initial


class MarketplaceRequestDetailView(DetailView):
    """
    Detailed marketplace view for request posted to the community hub
    """
    model = MarketplaceRequest
    context_object_name = 'marketplace_request'
    template_engine = 'mako'
    template_name = 'features/marketplace/marketplace_details.html'
