from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse
from django.utils import simplejson

import comment_client

class JsonResponse(HttpResponse):
    def __init__(self, data=None):
        content = simplejson.dumps(data,
                                   indent=2,
                                   ensure_ascii=False)
        super(JsonResponse, self).__init__(content,
                                           mimetype='application/json; charset=utf8')

class JsonError(HttpResponse):
    def __init__(self, status, error_message=""):
        content = simplejson.dumps({'errors': error_message},
                                   indent=2,
                                   ensure_ascii=False)
        super(JsonError, self).__init__(content,
                                           status=status,
                                           mimetype='application/json; charset=utf8')
        
def thread_author_only(fn):
    def verified_fn(request, *args, **kwargs):
        thread_id = args.get('thread_id', False) or \
                    kwargs.get('thread_id', False)
        thread = comment_client.get_thread(thread_id)
        if request.user.id == thread['user_id']:
            return fn(request, *args, **kwargs)
        else:
            return JsonError(400, "unauthorized")
    return verified_fn

def comment_author_only(fn):
    def verified_fn(request, *args, **kwargs):
        comment_id = args.get('comment_id', False) or \
                    kwargs.get('comment_id', False)
        comment = comment_client.get_comment(comment_id)
        if request.user.id == comment['user_id']:
            return fn(request, *args, **kwargs)
        else:
            return JsonError(400, "unauthorized")
    return verified_fn

def instructor_only(fn): #TODO add instructor verification
    return fn

def extract(dic, keys):
    return {k: dic[k] for k in keys}

@login_required
@require_POST
def create_thread(request, course_id, commentable_id):
    attributes = extract(request.POST, ['body', 'title'])
    attributes['user_id'] = request.user.id
    attributes['course_id'] = course_id
    response = comment_client.create_thread(commentable_id, attributes)
    return JsonResponse(response)

@thread_author_only
@login_required
@require_POST
def update_thread(request, course_id, thread_id):
    attributes = extract(request.POST, ['body', 'title'])
    response = comment_client.update_thread(thread_id, attributes)
    return JsonResponse(response)

@login_required
@require_POST
def create_comment(request, course_id, thread_id):
    attributes = extract(request.POST, ['body'])
    if request.POST.get('anonymous', 'false').lower() == 'false':
        attributes['user_id'] = request.user.id
    attributes['course_id'] = course_id
    attributes['auto_subscribe'] = bool(request.POST.get('autowatch', False))
    print attributes
    response = comment_client.create_comment(thread_id, attributes)
    return JsonResponse(response)

@thread_author_only
@login_required
@require_POST
def delete_thread(request, course_id, thread_id):
    response = comment_client.delete_thread(thread_id)
    return JsonResponse(response)

@thread_author_only
@login_required
@require_POST
def update_comment(request, course_id, comment_id):
    attributes = extract(request.POST, ['body'])
    response = comment_client.update_comment(comment_id, attributes)
    return JsonResponse(response)

@instructor_only
@login_required
@require_POST
def endorse_comment(request, course_id, comment_id):
    attributes = extract(request.POST, ['endorsed'])
    response = comment_client.update_comment(comment_id, attributes)
    return JsonResponse(response)

@login_required
@require_POST
def create_sub_comment(request, course_id, comment_id):
    attributes = extract(request.POST, ['body'])
    if request.POST.get('anonymous', 'false').lower() == 'false':
        attributes['user_id'] = request.user.id
    attributes['course_id'] = course_id
    attributes['auto_subscribe'] = bool(request.POST.get('autowatch', False))
    response = comment_client.create_sub_comment(comment_id, attributes)
    return JsonResponse(response)

@comment_author_only
@login_required
@require_POST
def delete_comment(request, course_id, comment_id):
    response = comment_client.delete_comment(comment_id)
    return JsonResponse(response)

@login_required
@require_POST
def vote_for_comment(request, course_id, comment_id, value):
    user_id = request.user.id
    response = comment_client.vote_for_comment(comment_id, user_id, value)
    return JsonResponse(response)

@login_required
@require_POST
def vote_for_thread(request, course_id, thread_id, value):
    user_id = request.user.id
    response = comment_client.vote_for_thread(thread_id, user_id, value)
    return JsonResponse(response)

@login_required
@require_POST
def watch_thread(request, course_id, thread_id):
    user_id = request.user.id
    response = comment_client.subscribe_thread(user_id, thread_id)
    return JsonResponse(response)

@login_required
@require_POST
def watch_commentable(request, course_id, commentable_id):
    user_id = request.user.id
    response = comment_client.subscribe_commentable(user_id, commentable_id)
    return JsonResponse(response)

@login_required
@require_POST
def follow(request, course_id, followed_user_id):
    user_id = request.user.id
    response = comment_client.follow(user_id, followed_user_id)
    return JsonResponse(response)

@login_required
@require_POST
def unwatch_thread(request, course_id, thread_id):
    user_id = request.user.id
    response = comment_client.unsubscribe_thread(user_id, thread_id)
    return JsonResponse(response)

@login_required
@require_POST
def unwatch_commentable(request, course_id, commentable_id):
    user_id = request.user.id
    response = comment_client.unsubscribe_commentable(user_id, commentable_id)
    return JsonResponse(response)

@login_required
@require_POST
def unfollow(request, course_id, followed_user_id):
    user_id = request.user.id
    response = comment_client.unfollow(user_id, followed_user_id)
    return JsonResponse(response)

@login_required
@require_GET
def search(request, course_id):
    text = request.GET.get('text', None)
    commentable_id = request.GET.get('commentable_id', None)
    response = comment_client.search(text, commentable_id)
    return JsonResponse(response)
