from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from edxmako.shortcuts import render_to_response

from .models import Job


class JobListView(ListView):

    model = Job
    context_object_name = 'job_list'
    paginate_by = 10
    template_name = 'features/job_board/job_list.html'
    ordering = ['-created']
    template_engine = 'mako'


class JobDetail(DetailView):
    model = Job
    template_engine = 'mako'
    template_name = 'features/job_board/job_detail.html'

    def get_context_data(self, **kwargs):
        job = self.get_object()
        context = {
            'title': job.title,
            'company': job.company,
            'type': job.type,
            'location': job.location,
            'hours': job.hours,
            'published': job.created.strftime('%B %d, %Y'),
            'description': job.description,
            'function': job.function,
            'responsibilities': job.responsibilities
        }
        return context
