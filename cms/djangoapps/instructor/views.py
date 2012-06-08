import logging

from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.contrib.auth import logout, authenticate, login
from django.shortcuts import redirect
from mitxmako.shortcuts import render_to_response

from django_future.csrf import ensure_csrf_cookie

log = logging.getLogger("mitx.student")


@require_http_methods(['GET', 'POST'])
def do_login(request):
    if request.method == 'POST':
        return post_login(request)
    elif request.method == 'GET':
        return get_login(request)


@require_POST
@ensure_csrf_cookie
def post_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return redirect(request.POST.get('next', '/'))
        else:
            raise Exception("Can't log in, account disabled")
    else:
        raise Exception("Can't log in, invalid authentication")


@require_GET
@ensure_csrf_cookie
def get_login(request):
    return render_to_response('login.html', {
        'next': request.GET.get('next')
    })


@ensure_csrf_cookie
def logout_user(request):
    ''' HTTP request to log in the user. Redirects to marketing page'''
    logout(request)
    return redirect('/')
