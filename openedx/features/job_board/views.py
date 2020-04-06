from django.shortcuts import get_object_or_404
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


def show_job_detail(request, job_id):
    job = get_object_or_404(
        Job,
        pk=job_id,
    )
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

    return render_to_response('features/job_board/job_detail.html', context)
