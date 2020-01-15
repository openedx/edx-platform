from edxmako.shortcuts import render_to_response


def list_specializations(request):

    """
    :param request:
    :return: list of active cards
    """
    return render_to_response('features/specializations/list.html', {})
