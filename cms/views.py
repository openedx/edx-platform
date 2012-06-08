from mitxmako.shortcuts import render_to_response


def calendar(request, course):
    return render_to_response('calendar.html', {})
