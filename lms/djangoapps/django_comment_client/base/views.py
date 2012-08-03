import time
import random
import os
import os.path
import logging
import urlparse

import comment_client

from django.core import exceptions
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators import csrf
from django.core.files.storage import get_storage_class
from django.utils.translation import ugettext as _
from django.conf import settings

from mitxmako.shortcuts import render_to_response, render_to_string
from django_comment_client.utils import JsonResponse, JsonError, extract

def thread_author_only(fn):
    def verified_fn(request, *args, **kwargs):
        thread_id = kwargs.get('thread_id', False)
        thread = comment_client.get_thread(thread_id)
        if str(request.user.id) == str(thread['user_id']):
            return fn(request, *args, **kwargs)
        else:
            return JsonError("unauthorized")
    return verified_fn

def comment_author_only(fn):
    def verified_fn(request, *args, **kwargs):
        comment_id = kwargs.get('comment_id', False)
        comment = comment_client.get_comment(comment_id)
        if str(request.user.id) == str(comment['user_id']):
            return fn(request, *args, **kwargs)
        else:
            return JsonError("unauthorized")
    return verified_fn

def instructor_only(fn):
    def verified_fn(request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonError("unauthorized")
        else:
            return fn(request, *args, **kwargs)
    return verified_fn

@login_required
@require_POST
def create_thread(request, course_id, commentable_id):
    attributes = extract(request.POST, ['body', 'title', 'tags'])
    attributes['user_id'] = request.user.id
    attributes['course_id'] = course_id
    if request.POST.get('anonymous', 'false').lower() == 'true':
        attributes['anonymous'] = True
    if request.POST.get('autowatch', 'false').lower() == 'true':
        attributes['auto_subscribe'] = True
    response = comment_client.create_thread(commentable_id, attributes)
    if request.is_ajax():
        context = {
            'course_id': course_id,
            'thread': response,
        }
        html = render_to_string('discussion/ajax_create_thread.html', context)
        return JsonResponse({
            'html': html,
            'content': response,
        })
    else:
        return JsonResponse(response)

@thread_author_only
@login_required
@require_POST
def update_thread(request, course_id, thread_id):
    attributes = extract(request.POST, ['body', 'title', 'tags'])
    response = comment_client.update_thread(thread_id, attributes)
    if request.is_ajax():
        context = {
            'thread': response,
            'course_id': course_id,
        }
        html = render_to_string('discussion/ajax_update_thread.html', context)
        return JsonResponse({
            'html': html,
            'content': response,
        })
    else:
        return JsonResponse(response)

def _create_comment(request, course_id, _response_from_attributes):
    attributes = extract(request.POST, ['body'])
    attributes['user_id'] = request.user.id
    attributes['course_id'] = course_id
    if request.POST.get('anonymous', 'false').lower() == 'true':
        attributes['anonymous'] = True
    if request.POST.get('autowatch', 'false').lower() == 'true':
        attributes['auto_subscribe'] = True
    response = _response_from_attributes(attributes)
    if request.is_ajax():
        context = {
            'comment': response,
        }
        html = render_to_string('discussion/ajax_create_comment.html', context)
        return JsonResponse({
            'html': html,
            'content': response,
        })
    else:
        return JsonResponse(response)

@login_required
@require_POST
def create_comment(request, course_id, thread_id):
    def _response_from_attributes(attributes):
        return comment_client.create_comment(thread_id, attributes)
    return _create_comment(request, course_id, _response_from_attributes)

@thread_author_only
@login_required
@require_POST
def delete_thread(request, course_id, thread_id):
    response = comment_client.delete_thread(thread_id)
    return JsonResponse(response)

@comment_author_only
@login_required
@require_POST
def update_comment(request, course_id, comment_id):
    attributes = extract(request.POST, ['body'])
    response = comment_client.update_comment(comment_id, attributes)
    if request.is_ajax():
        context = {
            'comment': response,
            'course_id': course_id,
        }
        html = render_to_string('discussion/ajax_update_comment.html', context)
        return JsonResponse({
            'html': html,
            'content': response,
        })
    else:
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
    def _response_from_attributes(attributes):
        return comment_client.create_sub_comment(comment_id, attributes)
    return _create_comment(request, course_id, _response_from_attributes)

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
def follow_thread(request, course_id, thread_id):
    user_id = request.user.id
    response = comment_client.subscribe_thread(user_id, thread_id)
    return JsonResponse(response)

@login_required
@require_POST
def follow_commentable(request, course_id, commentable_id):
    user_id = request.user.id
    response = comment_client.subscribe_commentable(user_id, commentable_id)
    return JsonResponse(response)

@login_required
@require_POST
def follow_user(request, course_id, followed_user_id):
    user_id = request.user.id
    response = comment_client.follow(user_id, followed_user_id)
    return JsonResponse(response)

@login_required
@require_POST
def unfollow_thread(request, course_id, thread_id):
    user_id = request.user.id
    response = comment_client.unsubscribe_thread(user_id, thread_id)
    return JsonResponse(response)

@login_required
@require_POST
def unfollow_commentable(request, course_id, commentable_id):
    user_id = request.user.id
    response = comment_client.unsubscribe_commentable(user_id, commentable_id)
    return JsonResponse(response)

@login_required
@require_POST
def unfollow_user(request, course_id, followed_user_id):
    user_id = request.user.id
    response = comment_client.unfollow(user_id, followed_user_id)
    return JsonResponse(response)

@require_GET
def search(request, course_id):
    text = request.GET.get('text', None)
    commentable_id = request.GET.get('commentable_id', None)
    tags = request.GET.get('tags', None)
    response = comment_client.search_threads({
        'text': text,
        'commentable_id': commentable_id,
        'tags': tags,
    })
    return JsonResponse(response)

@require_GET
def tags_autocomplete(request, course_id):
    value = request.GET.get('q', None)
    results = []
    if value:
        results = comment_client.tags_autocomplete(value)
    return JsonResponse(results)

@csrf.csrf_exempt
@login_required
@require_POST
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
