from edxmako.shortcuts import render_to_response


def list_specializations(request):
    return render_to_response('features/specializations/list.html', {})


def specialization_about(request, specialization_uuid):
    return render_to_response('features/specializations/about.html', {})
