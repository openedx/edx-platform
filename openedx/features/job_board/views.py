from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from edxmako.shortcuts import render_to_response

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView


from models import Job
from forms import JobForm


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


def add_job(request):
    add_job_template = 'features/job_board/add_job.html'

    if request.method == 'GET':
        return render_to_response(add_job_template, {'job_form': JobForm()})
    elif request.method == 'POST':
        submitted_job_form = JobForm(request.POST)

        if submitted_job_form.is_valid():
            submitted_job_form.save()
            return redirect(reverse('job_list'))

        return render_to_response(add_job_template, {'job_form': submitted_job_form})

