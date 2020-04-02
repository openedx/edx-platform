from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from edxmako.shortcuts import render_to_response

from forms import JobForm


def list_jobs(request):
    return render_to_response('features/job_board/job_list.html', {})


def show_job_detail(request):
    return render_to_response('features/job_board/job_detail.html', {})


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

