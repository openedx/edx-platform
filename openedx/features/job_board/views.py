from django.views.generic.list import ListView
from edxmako.shortcuts import render_to_response

from .models import Job


class JobsListView(ListView):

    model = Job
    context_object_name = 'jobs_list'
    paginate_by = 10
    template_name = 'features/job_board/job_list.html'
    ordering = ['-created']

    def get_context_data(self, **kwargs):
        context = super(JobsListView, self).get_context_data(**kwargs)
        context['job_count'] = Job.objects.all().count()
        return context


def show_job_detail(request):

    return render_to_response('features/job_board/job_detail.html', {})
