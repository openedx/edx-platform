from django.core.urlresolvers import reverse

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
