from mitxmako.shortcuts import render_to_response


def dev_mode(request):
    return render_to_response("dev/dev_mode.html")
