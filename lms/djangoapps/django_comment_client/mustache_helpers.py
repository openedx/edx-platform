from django.core.urlresolvers import reverse
import urllib

def pluralize(content, text):
    num, word = text.split(' ')
    if int(num or '0') >= 2:
        return num + ' ' + word + 's'
    else:
        return num + ' ' + word

def url_for_user(content, user_id):
    return reverse('django_comment_client.forum.views.user_profile', args=[content['course_id'], user_id])

def url_for_tags(content, tags): # assume that tags is in the format u'a, b, c'
    return reverse('django_comment_client.forum.views.forum_form_discussion', args=[content['course_id']]) + '?' + urllib.urlencode({'tags': tags})

def close_thread_text(content):
    if content.get('closed'):
        return 'Re-open thread'
    else:
        return 'Close thread'

mustache_helpers = {
    'pluralize': pluralize,
    'url_for_tags': url_for_tags,
    'url_for_user': url_for_user,
    'close_thread_text': close_thread_text,
}
