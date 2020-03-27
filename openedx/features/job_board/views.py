from edxmako.shortcuts import render_to_response


def list_jobs(request):

    return render_to_response('features/job_board/job_list.html', {})


def show_job_detail(request):

    return render_to_response('features/job_board/job_detail.html', {})
