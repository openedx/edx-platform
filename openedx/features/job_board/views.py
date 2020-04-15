from django.core.urlresolvers import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django_countries import countries

from .constants import (
    DJANGO_COUNTRIES_KEY_INDEX,
    DJANGO_COUNTRIES_VALUE_INDEX,
    JOB_COMP_HOURLY_INDEX,
    JOB_COMP_SALARIED_INDEX,
    JOB_COMP_VOLUNTEER_INDEX,
    JOB_COMPENSATION_CHOICES,
    JOB_HOURS_CHOICES,
    JOB_HOURS_FREELANCE_INDEX,
    JOB_HOURS_FULLTIME_INDEX,
    JOB_HOURS_PARTTIME_INDEX,
    JOB_PARAM_CITY_KEY,
    JOB_PARAM_COUNTRY_KEY,
    JOB_PARAM_QUERY_KEY,
    JOB_TUPLE_KEY_INDEX,
    JOB_TYPE_CHOICES,
    JOB_TYPE_ONSITE_INDEX,
    JOB_TYPE_REMOTE_INDEX
)
from .models import Job


class JobListView(ListView):
    model = Job
    context_object_name = 'job_list'
    paginate_by = 10
    template_name = 'features/job_board/job_list.html'
    ordering = ['-created']
    template_engine = 'mako'

    def get_queryset(self):
        params = self.request.GET

        query = params.get(JOB_PARAM_QUERY_KEY)
        city = params.get(JOB_PARAM_CITY_KEY)
        country = params.get(JOB_PARAM_COUNTRY_KEY)
        remote = params.get(JOB_TYPE_CHOICES[JOB_TYPE_REMOTE_INDEX][JOB_TUPLE_KEY_INDEX])
        onsite = params.get(JOB_TYPE_CHOICES[JOB_TYPE_ONSITE_INDEX][JOB_TUPLE_KEY_INDEX])
        fulltime = params.get(JOB_HOURS_CHOICES[JOB_HOURS_FULLTIME_INDEX][JOB_TUPLE_KEY_INDEX])
        parttime = params.get(JOB_HOURS_CHOICES[JOB_HOURS_PARTTIME_INDEX][JOB_TUPLE_KEY_INDEX])
        freelance = params.get(JOB_HOURS_CHOICES[JOB_HOURS_FREELANCE_INDEX][JOB_TUPLE_KEY_INDEX])
        volunteer = params.get(JOB_COMPENSATION_CHOICES[JOB_COMP_VOLUNTEER_INDEX][JOB_TUPLE_KEY_INDEX])
        hourly = params.get(JOB_COMPENSATION_CHOICES[JOB_COMP_HOURLY_INDEX][JOB_TUPLE_KEY_INDEX])
        salaried = params.get(JOB_COMPENSATION_CHOICES[JOB_COMP_SALARIED_INDEX][JOB_TUPLE_KEY_INDEX])

        job_type_list = [job_type for job_type in (
            JOB_TYPE_CHOICES[JOB_TYPE_REMOTE_INDEX][JOB_TUPLE_KEY_INDEX] if remote else [],
            JOB_TYPE_CHOICES[JOB_TYPE_ONSITE_INDEX][JOB_TUPLE_KEY_INDEX] if onsite else [])
                         if job_type]

        job_hours_list = [job_hours for job_hours in (
            JOB_HOURS_CHOICES[JOB_HOURS_FULLTIME_INDEX][JOB_TUPLE_KEY_INDEX] if fulltime else [],
            JOB_HOURS_CHOICES[JOB_HOURS_PARTTIME_INDEX][JOB_TUPLE_KEY_INDEX] if parttime else [],
            JOB_HOURS_CHOICES[JOB_HOURS_FREELANCE_INDEX][JOB_TUPLE_KEY_INDEX] if freelance else [])
                          if job_hours]

        job_compensation_list = [job_comp for job_comp in (
            JOB_COMPENSATION_CHOICES[JOB_COMP_VOLUNTEER_INDEX][JOB_TUPLE_KEY_INDEX] if volunteer else [],
            JOB_COMPENSATION_CHOICES[JOB_COMP_HOURLY_INDEX][JOB_TUPLE_KEY_INDEX] if hourly else [],
            JOB_COMPENSATION_CHOICES[JOB_COMP_SALARIED_INDEX][JOB_TUPLE_KEY_INDEX] if salaried else [])
                                 if job_comp]

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
            'remote': params.get(JOB_TYPE_CHOICES[JOB_TYPE_REMOTE_INDEX][JOB_TUPLE_KEY_INDEX]),
            'onsite': params.get(JOB_TYPE_CHOICES[JOB_TYPE_ONSITE_INDEX][JOB_TUPLE_KEY_INDEX]),
            'city': params.get(JOB_PARAM_CITY_KEY),
            'country': params.get(JOB_PARAM_COUNTRY_KEY),
            'fulltime': params.get(JOB_HOURS_CHOICES[JOB_HOURS_FULLTIME_INDEX][JOB_TUPLE_KEY_INDEX]),
            'parttime': params.get(JOB_HOURS_CHOICES[JOB_HOURS_PARTTIME_INDEX][JOB_TUPLE_KEY_INDEX]),
            'freelance': params.get(JOB_HOURS_CHOICES[JOB_HOURS_FREELANCE_INDEX][JOB_TUPLE_KEY_INDEX]),
            'volunteer': params.get(JOB_COMPENSATION_CHOICES[JOB_COMP_VOLUNTEER_INDEX][JOB_TUPLE_KEY_INDEX]),
            'hourly': params.get(JOB_COMPENSATION_CHOICES[JOB_COMP_HOURLY_INDEX][JOB_TUPLE_KEY_INDEX]),
            'salaried': params.get(JOB_COMPENSATION_CHOICES[JOB_COMP_SALARIED_INDEX][JOB_TUPLE_KEY_INDEX]),
        }

        context['filtered'] = any(context['search_fields'].values())

        return context


class JobDetailView(DetailView):
    model = Job
    template_engine = 'mako'
    template_name = 'features/job_board/job_detail.html'


class JobCreateView(CreateView):
    model = Job
    fields = '__all__'
    template_name = 'features/job_board/create_job_form.html'

    def get_success_url(self):
        return reverse('job_list')
