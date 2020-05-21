# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import operator

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View, generic
from django.views.generic.list import ListView
from django_countries import countries

from edxmako.shortcuts import render_to_response
from openedx.features.marketplace.decorators import has_affiliated_user
from openedx.features.marketplace.forms import MarketplaceRequestForm

from .constants import (
    DJANGO_COUNTRIES_KEY_INDEX,
    DJANGO_COUNTRIES_VALUE_INDEX,
    MARKETPLACE_PARAM_CITY_KEY,
    MARKETPLACE_PARAM_COUNTRY_KEY,
    MARKETPLACE_PARAM_QUERY_KEY,
    ORGANIZATIONAL_PROBLEM_CHOICES_VIEW,
    ORGANIZATIONAL_PROBLEM_TYPE_DELIVERY_SERVICES_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_FUNDING_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_HUMAN_RESOURCES_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_MENTORSHIP_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_ONLINE_TRAINING_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_OTHER_KEY,
    ORGANIZATIONAL_PROBLEM_TYPE_REMOTE_WORKING_TOOLS_KEY,
    ORGANIZATIONAL_SECTOR_ART_AND_CULTURE,
    ORGANIZATIONAL_SECTOR_CLEAN_ENERGY,
    ORGANIZATIONAL_SECTOR_CLIMATE_CHANGES,
    ORGANIZATIONAL_SECTOR_EDUCATION,
    ORGANIZATIONAL_SECTOR_ENVIRONMENTAL_CONSERVATION,
    ORGANIZATIONAL_SECTOR_GENDER_EQUALITY,
    ORGANIZATIONAL_SECTOR_HEALTH_AND_WELL_BEING,
    ORGANIZATIONAL_SECTOR_HUMAN_RIGHTS,
    ORGANIZATIONAL_SECTOR_OTHER_KEY,
    ORGANIZATIONAL_SECTOR_SANITATION,
    ORGANIZATIONAL_SECTOR_SOCIAL_JUSTICE,
    ORGANIZATIONAL_SECTOR_WORK_AND_ECONOMIC_GROWTH,
    ORGANIZATION_SECTOR_CHOICES_VIEW
)
from .models import MarketplaceRequest


class MarketplaceListView(ListView):
    model = MarketplaceRequest
    context_object_name = 'marketplace_list'
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
        tuple_key_index = 0
        return [choice[tuple_key_index] for choice in choices if params.get(choice[tuple_key_index])]

    def get_queryset(self):
        params = self.request.GET

        query = params.get(MARKETPLACE_PARAM_QUERY_KEY)
        city = params.get(MARKETPLACE_PARAM_CITY_KEY)
        country = params.get(MARKETPLACE_PARAM_COUNTRY_KEY)

        request_type_list = self.get_checked_choices(ORGANIZATIONAL_PROBLEM_CHOICES_VIEW)
        organizational_sector_list = self.get_checked_choices(ORGANIZATION_SECTOR_CHOICES_VIEW)
        queryset = super(MarketplaceListView, self).get_queryset()

        if request_type_list:
            # has other problem selected
            if ORGANIZATIONAL_PROBLEM_TYPE_OTHER_KEY in request_type_list:
                queryset = queryset.filter(reduce(operator.or_, (~Q(organizational_problems__endswith='|')
                                                                 | Q(organizational_problems__contains=x)
                                                                 for x in request_type_list)))
            else:
                queryset = queryset.filter(reduce(operator.or_, (Q(organizational_problems__contains=x)
                                                                 for x in request_type_list)))
        if organizational_sector_list:
            # has other sector selected
            if ORGANIZATIONAL_SECTOR_OTHER_KEY in organizational_sector_list:
                queryset = queryset.filter(reduce(operator.or_, (~Q(organization_sector__endswith='|')
                                                                 | Q(organization_sector__contains=x)
                                                                 for x in organizational_sector_list)))
            else:
                queryset = queryset.filter(reduce(operator.or_, (Q(organization_sector__contains=x)
                                                                 for x in organizational_sector_list)))

        if country:
            country_codes = [django_country[DJANGO_COUNTRIES_KEY_INDEX] for django_country in countries if
                             country.lower() in django_country[DJANGO_COUNTRIES_VALUE_INDEX].lower()]
            queryset = queryset.filter(country__in=country_codes)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if query:
            queryset = queryset.filter(organization_mission__icontains=query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(MarketplaceListView, self).get_context_data(**kwargs)
        params = self.request.GET

        context['search_fields'] = {
            'query': params.get(MARKETPLACE_PARAM_QUERY_KEY),
            'city': params.get(MARKETPLACE_PARAM_CITY_KEY),
            'country': params.get(MARKETPLACE_PARAM_COUNTRY_KEY),
            'delivery-services': params.get(ORGANIZATIONAL_PROBLEM_TYPE_DELIVERY_SERVICES_KEY),
            'funding': params.get(ORGANIZATIONAL_PROBLEM_TYPE_FUNDING_KEY),
            'healthcare-supplies': params.get(ORGANIZATIONAL_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES_KEY),
            'human-resources': params.get(ORGANIZATIONAL_PROBLEM_TYPE_HUMAN_RESOURCES_KEY),
            'mentorship': params.get(ORGANIZATIONAL_PROBLEM_TYPE_MENTORSHIP_KEY),
            'online-training': params.get(ORGANIZATIONAL_PROBLEM_TYPE_ONLINE_TRAINING_KEY),
            'remote-working-tools': params.get(ORGANIZATIONAL_PROBLEM_TYPE_REMOTE_WORKING_TOOLS_KEY),
            'health-and-well-being': params.get(ORGANIZATIONAL_SECTOR_HEALTH_AND_WELL_BEING),
            'education': params.get(ORGANIZATIONAL_SECTOR_EDUCATION),
            'gender-equality': params.get(ORGANIZATIONAL_SECTOR_GENDER_EQUALITY),
            'sanitation': params.get(ORGANIZATIONAL_SECTOR_SANITATION),
            'climate-changes': params.get(ORGANIZATIONAL_SECTOR_CLIMATE_CHANGES),
            'clean-energy': params.get(ORGANIZATIONAL_SECTOR_CLEAN_ENERGY),
            'environmental-conservation': params.get(ORGANIZATIONAL_SECTOR_ENVIRONMENTAL_CONSERVATION),
            'work-and-economic-growth': params.get(ORGANIZATIONAL_SECTOR_WORK_AND_ECONOMIC_GROWTH),
            'human-rights': params.get(ORGANIZATIONAL_SECTOR_HUMAN_RIGHTS),
            'social-justice': params.get(ORGANIZATIONAL_SECTOR_SOCIAL_JUSTICE),
            'art-and-culture': params.get(ORGANIZATIONAL_SECTOR_ART_AND_CULTURE),
            'other-sector': params.get(ORGANIZATIONAL_SECTOR_OTHER_KEY),
            'other-problem': params.get(ORGANIZATIONAL_PROBLEM_TYPE_OTHER_KEY),
        }

        context['filtered'] = any(context['search_fields'].values())

        return context


@method_decorator(has_affiliated_user, name='dispatch')
class MarketplaceCreateRequestView(generic.CreateView, LoginRequiredMixin):
    form_class = MarketplaceRequestForm
    template_name = 'features/marketplace/markertplace_request_form.html'

    def get_success_url(self):
        return reverse('marketplace-listing')

    def get_initial(self, *args, **kwargs):
        initial = super(MarketplaceCreateRequestView, self).get_initial(**kwargs)
        user = self.request.user
        initial['user'] = user
        initial['organization'] = user.extended_profile.organization
        return initial


class MarketplaceRequestDetailView(View):
    template_name = 'features/marketplace/marketplace_details.html'

    def get(self, request, *args, **kwargs):
        marketplace_request = get_object_or_404(MarketplaceRequest, pk=kwargs['pk'])
        context = {'marketplace_request': marketplace_request}
        return render_to_response(self.template_name, context)
