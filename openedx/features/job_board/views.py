from django.core.urlresolvers import reverse

from django_countries import countries

from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Job
from .constants import DJANGO_COUNTRIES_VALUE_INDEX, DJANGO_COUNTRIES_KEY_INDEX, JOB_TYPE_REMOTE_INDEX, \
    JOB_TYPE_CHOICES, JOB_HOURS_CHOICES, JOB_COMPENSATION_CHOICES, JOB_COMP_HOURLY_INDEX, JOB_COMP_SALARIED_INDEX, \
    JOB_COMP_VOLUNTEER_INDEX, JOB_HOURS_FREELANCE_INDEX, JOB_HOURS_FULLTIME_INDEX, JOB_HOURS_PARTTIME_INDEX, \
    JOB_TYPE_ONSITE_INDEX, JOB_TUPLE_KEY_INDEX, JOB_PARAM_CITY_KEY, JOB_PARAM_COUNTRY_KEY, JOB_PARAM_QUERY_KEY


class JobListView(ListView):
    model = Job
    context_object_name = 'job_list'
    paginate_by = 10
    template_name = 'features/job_board/job_list.html'
    ordering = ['-created']
    template_engine = 'mako'

    def get_queryset(self):
        param = self.request.GET

        param_query = param.get(JOB_PARAM_QUERY_KEY)
        param_city = param.get(JOB_PARAM_CITY_KEY)
        param_country = param.get(JOB_PARAM_COUNTRY_KEY)
        param_remote = param.get(JOB_TYPE_CHOICES[JOB_TYPE_REMOTE_INDEX][JOB_TUPLE_KEY_INDEX])
        param_onsite = param.get(JOB_TYPE_CHOICES[JOB_TYPE_ONSITE_INDEX][JOB_TUPLE_KEY_INDEX])
        param_fulltime = param.get(JOB_HOURS_CHOICES[JOB_HOURS_FULLTIME_INDEX][JOB_TUPLE_KEY_INDEX])
        param_parttime = param.get(JOB_HOURS_CHOICES[JOB_HOURS_PARTTIME_INDEX][JOB_TUPLE_KEY_INDEX])
        param_freelance = param.get(JOB_HOURS_CHOICES[JOB_HOURS_FREELANCE_INDEX][JOB_TUPLE_KEY_INDEX])
        param_volunteer = param.get(JOB_COMPENSATION_CHOICES[JOB_COMP_VOLUNTEER_INDEX][JOB_TUPLE_KEY_INDEX])
        param_hourly = param.get(JOB_COMPENSATION_CHOICES[JOB_COMP_HOURLY_INDEX][JOB_TUPLE_KEY_INDEX])
        param_salaried = param.get(JOB_COMPENSATION_CHOICES[JOB_COMP_SALARIED_INDEX][JOB_TUPLE_KEY_INDEX])

        job_type_list = [job_type for job_type in (
            JOB_TYPE_CHOICES[JOB_TYPE_REMOTE_INDEX][JOB_TUPLE_KEY_INDEX] if param_remote else [],
            JOB_TYPE_CHOICES[JOB_TYPE_ONSITE_INDEX][JOB_TUPLE_KEY_INDEX] if param_onsite else []) if job_type]

        job_hours_list = [job_hours for job_hours in (
            JOB_HOURS_CHOICES[JOB_HOURS_FULLTIME_INDEX][JOB_TUPLE_KEY_INDEX] if param_fulltime else [],
            JOB_HOURS_CHOICES[JOB_HOURS_PARTTIME_INDEX][JOB_TUPLE_KEY_INDEX] if param_parttime else [],
            JOB_HOURS_CHOICES[JOB_HOURS_FREELANCE_INDEX][JOB_TUPLE_KEY_INDEX] if param_freelance else []) if job_hours]

        job_compensation_list = [job_comp for job_comp in (
            JOB_COMPENSATION_CHOICES[JOB_COMP_VOLUNTEER_INDEX][JOB_TUPLE_KEY_INDEX] if param_volunteer else [],
            JOB_COMPENSATION_CHOICES[JOB_COMP_HOURLY_INDEX][JOB_TUPLE_KEY_INDEX] if param_hourly else [],
            JOB_COMPENSATION_CHOICES[JOB_COMP_SALARIED_INDEX][JOB_TUPLE_KEY_INDEX] if param_salaried else []) if job_comp]

        country_codes = []
        if param_country:
            country_codes = [country[DJANGO_COUNTRIES_KEY_INDEX] for country in countries if
                             param_country.lower() in country[DJANGO_COUNTRIES_VALUE_INDEX].lower()]

        queryset = super(JobListView, self).get_queryset()

        if job_type_list:
            queryset = queryset.filter(type__in=job_type_list)
        if job_hours_list:
            queryset = queryset.filter(hours__in=job_hours_list)
        if job_compensation_list:
            queryset = queryset.filter(compensation__in=job_compensation_list)
        if country_codes:
            queryset = queryset.filter(country__in=country_codes)
        if param_city:
            queryset = queryset.filter(city__icontains=param_city)
        if param_query:
            queryset = queryset.filter(title__icontains=param_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(JobListView, self).get_context_data(**kwargs)

        param = self.request.GET

        context['search_fields'] = {
            'query': param.get(JOB_PARAM_QUERY_KEY),
            'remote': param.get(JOB_TYPE_CHOICES[JOB_TYPE_REMOTE_INDEX][JOB_TUPLE_KEY_INDEX]),
            'onsite': param.get(JOB_TYPE_CHOICES[JOB_TYPE_ONSITE_INDEX][JOB_TUPLE_KEY_INDEX]),
            'city': param.get(JOB_PARAM_CITY_KEY),
            'country': param.get(JOB_PARAM_COUNTRY_KEY),
            'fulltime': param.get(JOB_HOURS_CHOICES[JOB_HOURS_FULLTIME_INDEX][JOB_TUPLE_KEY_INDEX]),
            'parttime': param.get(JOB_HOURS_CHOICES[JOB_HOURS_PARTTIME_INDEX][JOB_TUPLE_KEY_INDEX]),
            'freelance': param.get(JOB_HOURS_CHOICES[JOB_HOURS_FREELANCE_INDEX][JOB_TUPLE_KEY_INDEX]),
            'volunteer': param.get(JOB_COMPENSATION_CHOICES[JOB_COMP_VOLUNTEER_INDEX][JOB_TUPLE_KEY_INDEX]),
            'hourly': param.get(JOB_COMPENSATION_CHOICES[JOB_COMP_HOURLY_INDEX][JOB_TUPLE_KEY_INDEX]),
            'salaried': param.get(JOB_COMPENSATION_CHOICES[JOB_COMP_SALARIED_INDEX][JOB_TUPLE_KEY_INDEX]),
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
