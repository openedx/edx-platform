from edxmako.shortcuts import render_to_response


def g2a_dashboard(request):
    return render_to_response('partners/g2a/dashboard.html')
