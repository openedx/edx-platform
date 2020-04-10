import re
from django.core.urlresolvers import reverse

from django_countries import countries

from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from models import Job


class JobListView(ListView):
    model = Job
    context_object_name = 'job_list'
    paginate_by = 10
    template_name = 'features/job_board/job_list.html'
    ordering = ['-created']
    template_engine = 'mako'

    def get_queryset(self):
        self.param_job_query = self.request.GET.get('query')
        self.param_job_type = self.request.GET.getlist('type')
        self.param_job_city = self.request.GET.get('city')
        self.param_job_country = self.request.GET.get('country')
        self.param_job_hours = self.request.GET.getlist('hours')
        self.param_job_compensation = self.request.GET.getlist('compensation')

        if self.param_job_country:
            country_codes = [country[0] for country in countries if
                             self. param_job_country.lower() in country[1].lower()]

        queryset = super(JobListView, self).get_queryset()

        if self.param_job_type:
            queryset = queryset.filter(type__in=self.param_job_type)
        if self.param_job_hours:
            queryset = queryset.filter(hours__in=self.param_job_hours)
        if self.param_job_compensation:
            queryset = queryset.filter(compensation__in=self.param_job_compensation)
        if country_codes:
            queryset = queryset.filter(country__in__exact=country_codes)
        if self.param_job_city:
            queryset = queryset.filter(city__icontains=self.param_job_city)
        if self.param_job_query:
            queryset = queryset.filter(title__icontains=self.param_job_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(JobListView, self).get_context_data(**kwargs)

        context['remote'] = True if 'remote' in self.param_job_type else False
        context['onsite'] = True if 'onsite' in self.param_job_type else False
        context['volunteer'] = True if 'volunteer' in self.param_job_compensation else False
        context['hourly'] = True if 'hourly' in self.param_job_compensation else False
        context['salaried'] = True if 'salaried' in self.param_job_compensation else False
        context['fulltime'] = True if 'fulltime' in self.param_job_hours else False
        context['parttime'] = True if 'parttime' in self.param_job_hours else False
        context['freelance'] = True if 'freelance' in self.param_job_hours else False
        context['country'] = self.param_job_country if self.param_job_country else None
        context['city'] = self.param_job_city if self.param_job_city else None

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
