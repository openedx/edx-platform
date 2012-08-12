import time
import random
import os
import os.path
import logging
import urlparse

import comment_client as c

from django.core import exceptions
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators import csrf
from django.core.files.storage import get_storage_class
from django.utils.translation import ugettext as _
from django.conf import settings

from mitxmako.shortcuts import render_to_response, render_to_string
from django_comment_client.utils import JsonResponse, JsonError, extract

from django_comment_client.permissions import check_permissions_by_view
from collection import defaultdict
import functools

def permitted(fn):
    @functools.wraps(fn)
    def wrapper(request, *args, **kwargs):
        def fetch_content():
            if "thread_id" in kwargs:
                content = dict(c.Thread.find(kwargs["thread_id"]))
            elif "comment_id" in kwargs:
                content = dict(c.Comment.find(kwargs["comment_id"]))
            else:
                content = None
            return content

        if check_permissions_by_view(request.user, kwargs['course_id'], fetch_content(), request.view_name):
            return fn(request, *args, **kwargs)
        else:
            return JsonError("unauthorized")
    return wrapper

@require_POST
@login_required
@permitted
def create_thread(request, course_id, commentable_id):
    post = request.POST
    thread = c.Thread(**extract(post, ['body', 'title', 'tags']))
    thread.anonymous = post.get('anonymous', 'false').lower() == 'true'
    thread.course_id = course_id
    thread.user_id = request.user.id
    thread.save()
    if post.get('auto_subscribe', 'false').lower() == 'true':
        user = c.User.from_django_user(request.user)
        user.subscribe(thread)
    if request.is_ajax():
        context = {
            'course_id': course_id,
            'thread': dict(thread),
        }
        html = render_to_string('discussion/ajax_create_thread.html', context)
        return JsonResponse({
            'html': html,
            'content': dict(thread),
        })
    else:
        return JsonResponse(dict(thread))

@require_POST
@login_required
@permitted
def update_thread(request, course_id, thread_id):
    thread = c.Thread.find(thread_id)
    thread.update_attributes(**extract(request.POST, ['body', 'title', 'tags']))
    thread.save()
    if request.is_ajax():
        context = {
            'thread': dict(thread),
            'course_id': course_id,
        }
        html = render_to_string('discussion/ajax_update_thread.html', context)
        return JsonResponse({
            'html': html,
            'content': dict(thread),
        })
    else:
        return JsonResponse(dict(thread))

def _create_comment(request, course_id, thread_id=None, parent_id=None):
    post = request.POST
    comment = c.Comment(**extract(post, ['body']))
    comment.anonymous = post.get('anonymous', 'false').lower() == 'true'
    comment.user_id = request.user.id
    comment.course_id = course_id
    comment.thread_id = thread_id
    comment.parent_id = parent_id
    comment.save()
    dict_comment = dict(comment)
    if post.get('auto_subscribe', 'false').lower() == 'true':
        user = c.User.from_django_user(request.user)
        user.subscribe(comment.thread)
    if request.is_ajax():
        context = {
            'comment': dict(comment),
        }
        html = render_to_string('discussion/ajax_create_comment.html', context)
        return JsonResponse({
            'html': html,
            'content': dict(comment),
        })
    else:
        return JsonResponse(dict(comment))

@require_POST
@login_required
@permitted
def create_comment(request, course_id, thread_id):
    return _create_comment(request, course_id, thread_id=thread_id)

@require_POST
@login_required
@permitted
def delete_thread(request, course_id, thread_id):
    thread = c.Thread.find(thread_id)
    thread.delete()
    return JsonResponse(dict(thread))

@require_POST
@login_required
@permitted
def update_comment(request, course_id, comment_id):
    comment = c.Comment.find(comment_id)
    comment.update_attributes(**extract(request.POST, ['body']))
    comment.save()
    if request.is_ajax():
        context = {
            'comment': dict(comment),
            'course_id': course_id,
        }
        html = render_to_string('discussion/ajax_update_comment.html', context)
        return JsonResponse({
            'html': html,
            'content': dict(comment),
        })
    else:
        return JsonResponse(dict(comment)),

@require_POST
@login_required
@permitted
def endorse_comment(request, course_id, comment_id):
    comment = c.Comment.find(comment_id)
    comment.endorsed = request.POST.get('endorsed', 'false').lower() == 'true'
    comment.save()
    return JsonResponse(dict(response))

@require_POST
@login_required
@permitted
def openclose_thread(request, course_id, thread_id):
    comment = c.Comment.find(comment_id)
    comment.endorsed = request.POST.get('closed', 'false').lower() == 'true'
    comment.save()
    return JsonResponse(dict(response))

@require_POST
@login_required
@permitted
def create_sub_comment(request, course_id, comment_id):
    return _create_comment(request, course_id, parent_id=comment_id)

@require_POST
@login_required
@permitted
def delete_comment(request, course_id, comment_id):
    comment = c.Comment.find(comment_id)
    comment.delete()
    return JsonResponse(dict(response))

@require_POST
@login_required
@permitted
def vote_for_comment(request, course_id, comment_id, value):
    user = c.User.from_django_user(request.user)
    comment = c.Comment.find(comment_id)
    user.vote(comment, value)
    return JsonResponse(dict(comment))

@require_POST
@login_required
@permitted
def undo_vote_for_comment(request, course_id, comment_id):
    user = c.User.from_django_user(request.user)
    comment = c.Comment.find(comment_id)
    user.unvote(comment)
    return JsonResponse(dict(comment))

@require_POST
@login_required
@permitted
def vote_for_thread(request, course_id, thread_id, value):
    user = c.User.from_django_user(request.user)
    thread = c.Thread.find(thread_id)
    user.vote(thread, value)
    return JsonResponse(dict(thread))

@require_POST
@login_required
@permitted
def undo_vote_for_thread(request, course_id, thread_id):
    user = c.User.from_django_user(request.user)
    thread = c.Thread.find(thread_id)
    user.unvote(thread)
    return JsonResponse(dict(thread))
    

@require_POST
@login_required
@permitted
def follow_thread(request, course_id, thread_id):
    user = c.User.from_django_user(request.user)
    thread = c.Thread.find(thread_id)
    user.follow(thread)
    return JsonResponse({})

@require_POST
@login_required
@permitted
def follow_commentable(request, course_id, commentable_id):
    user = c.User.from_django_user(request.user)
    commentable = c.Commentable.find(commentable_id)
    user.follow(commentable)
    return JsonResponse({})

@require_POST
@login_required
@permitted
def follow_user(request, course_id, followed_user_id):
    user = c.User.from_django_user(request.user)
    followed_user = c.User.find(followed_user_id)
    user.follow(followed_user)
    return JsonResponse({})

@require_POST
@login_required
@permitted
def unfollow_thread(request, course_id, thread_id):
    user = c.User.from_django_user(request.user)
    thread = c.Thread.find(thread_id)
    user.unfollow(thread)
    return JsonResponse({})

@require_POST
@login_required
@permitted
def unfollow_commentable(request, course_id, commentable_id):
    user = c.User.from_django_user(request.user)
    commentable = c.Commentable.find(commentable_id)
    user.unfollow(commentable)
    return JsonResponse({})

@require_POST
@login_required
@permitted
def unfollow_user(request, course_id, followed_user_id):
    user = c.User.from_django_user(request.user)
    followed_user = c.User.find(followed_user_id)
    user.unfollow(followed_user)
    return JsonResponse({})

@require_GET
def search_similar_threads(request, course_id, commentable_id):
    text = request.GET.get('text', None)
    if text:
        return JsonResponse(
                c.search_similar_threads(
                    course_id,
                    recursive=False,
                    query_params={
                        'text': text,
                        'commentable_id': commentable_id,
                    },
                ))
    else:
        return JsonResponse([])

@require_GET
def tags_autocomplete(request, course_id):
    value = request.GET.get('q', None)
    results = []
    if value:
        results = c.tags_autocomplete(value)
    return JsonResponse(results)

@require_POST
@login_required
@csrf.csrf_exempt
def upload(request, course_id):#ajax upload file to a question or answer 
    """view that handles file upload via Ajax
    """

    # check upload permission
    result = ''
    error = ''
    new_file_name = ''
    try:
        # TODO authorization
        #may raise exceptions.PermissionDenied 
        #if request.user.is_anonymous():
        #    msg = _('Sorry, anonymous users cannot upload files')
        #    raise exceptions.PermissionDenied(msg)

        #request.user.assert_can_upload_file()

        # check file type
        f = request.FILES['file-upload']
        file_extension = os.path.splitext(f.name)[1].lower()
        if not file_extension in settings.DISCUSSION_ALLOWED_UPLOAD_FILE_TYPES:
            file_types = "', '".join(settings.DISCUSSION_ALLOWED_UPLOAD_FILE_TYPES)
            msg = _("allowed file types are '%(file_types)s'") % \
                    {'file_types': file_types}
            raise exceptions.PermissionDenied(msg)

        # generate new file name
        new_file_name = str(
                            time.time()
                        ).replace(
                            '.', 
                            str(random.randint(0,100000))
                        ) + file_extension

        file_storage = get_storage_class()()
        # use default storage to store file
        file_storage.save(new_file_name, f)
        # check file size
        # byte
        size = file_storage.size(new_file_name)
        if size > settings.ASKBOT_MAX_UPLOAD_FILE_SIZE:
            file_storage.delete(new_file_name)
            msg = _("maximum upload file size is %(file_size)sK") % \
                    {'file_size': settings.ASKBOT_MAX_UPLOAD_FILE_SIZE}
            raise exceptions.PermissionDenied(msg)

    except exceptions.PermissionDenied, e:
        error = unicode(e)
    except Exception, e:
        logging.critical(unicode(e))
        error = _('Error uploading file. Please contact the site administrator. Thank you.')

    if error == '':
        result = 'Good'
        file_url = file_storage.url(new_file_name)
        parsed_url = urlparse.urlparse(file_url)
        file_url = urlparse.urlunparse(
            urlparse.ParseResult(
                parsed_url.scheme, 
                parsed_url.netloc,
                parsed_url.path,
                '', '', ''
            )
        )
    else:
        result = ''
        file_url = ''

    return JsonResponse({
        'result': {
            'msg': result,
            'error': error,
            'file_url': file_url,
        }
    })
