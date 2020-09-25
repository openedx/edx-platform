"""
Views for Job Board app
"""
from django.core.urlresolvers import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django_countries import countries

from openedx.features.teams.helpers import USER_ICON_COLORS
from .constants import (
    DJANGO_COUNTRIES_KEY_INDEX,
    DJANGO_COUNTRIES_VALUE_INDEX,
    JOB_COMP_HOURLY_KEY,
    JOB_COMP_SALARIED_KEY,
    JOB_COMP_VOLUNTEER_KEY,
    JOB_COMPENSATION_CHOICES,
    JOB_HOURS_CHOICES,
    JOB_HOURS_FREELANCE_KEY,
    JOB_HOURS_FULLTIME_KEY,
    JOB_HOURS_PARTTIME_KEY,
    JOB_PARAM_CITY_KEY,
    JOB_PARAM_COUNTRY_KEY,
    JOB_PARAM_QUERY_KEY,
    JOB_TYPE_CHOICES,
    JOB_TYPE_ONSITE_KEY,
    JOB_TYPE_REMOTE_KEY
)
from .forms import JobCreationForm
from .models import Job


class JobListView(ListView):
    """
    To render jobs as a list view
    """
    model = Job
    context_object_name = 'job_list'
    paginate_by = 10
    template_name = 'features/job_board/job_list.html'
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

        query = params.get(JOB_PARAM_QUERY_KEY)
        city = params.get(JOB_PARAM_CITY_KEY)
        country = params.get(JOB_PARAM_COUNTRY_KEY)

        job_type_list = self.get_checked_choices(JOB_TYPE_CHOICES)
        job_hours_list = self.get_checked_choices(JOB_HOURS_CHOICES)
        job_compensation_list = self.get_checked_choices(JOB_COMPENSATION_CHOICES)

        queryset = super(JobListView, self).get_queryset()

        if job_type_list:
            queryset = queryset.filter(type__in=job_type_list)
        if job_hours_list:
            queryset = queryset.filter(hours__in=job_hours_list)
        if job_compensation_list:
            queryset = queryset.filter(compensation__in=job_compensation_list)
        if country:
            country_codes = [django_country[DJANGO_COUNTRIES_KEY_INDEX] for django_country in countries if
                             country.lower() in django_country[DJANGO_COUNTRIES_VALUE_INDEX].lower()]
            queryset = queryset.filter(country__in=country_codes)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if query:
            queryset = queryset.filter(title__icontains=query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(JobListView, self).get_context_data(**kwargs)

        params = self.request.GET

        context['search_fields'] = {
            'query': params.get(JOB_PARAM_QUERY_KEY),
            'remote': params.get(JOB_TYPE_REMOTE_KEY),
            'onsite': params.get(JOB_TYPE_ONSITE_KEY),
            'city': params.get(JOB_PARAM_CITY_KEY),
            'country': params.get(JOB_PARAM_COUNTRY_KEY),
            'fulltime': params.get(JOB_HOURS_FULLTIME_KEY),
            'parttime': params.get(JOB_HOURS_PARTTIME_KEY),
            'freelance': params.get(JOB_HOURS_FREELANCE_KEY),
            'volunteer': params.get(JOB_COMP_VOLUNTEER_KEY),
            'hourly': params.get(JOB_COMP_HOURLY_KEY),
            'salaried': params.get(JOB_COMP_SALARIED_KEY),
        }

        context['filtered'] = any(context['search_fields'].values())
        context['ICON_BACKGROUND_COLOR'] = USER_ICON_COLORS

        return context


class JobDetailView(DetailView):
    model = Job
    template_engine = 'mako'
    template_name = 'features/job_board/job_detail.html'


class JobCreateView(CreateView):
    form_class = JobCreationForm
    template_name = 'features/job_board/create_job_form.html'

    def get_success_url(self):
        return reverse('job_list')
