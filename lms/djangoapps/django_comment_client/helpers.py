from django.core.urlresolvers import reverse
from mitxmako.shortcuts import render_to_string
import urllib

def pluralize(singular_term, count):
    if int(count) >= 2:
        return singular_term + 's'
    return singular_term

def show_if(text, condition):
    if condition:
        return text
    else:
        return ''

def close_thread_text(content):
    if content.get('closed'):
        return 'Re-open thread'
    else:
        return 'Close thread'

def url_for_user(course_id, user_id):
    return reverse('django_comment_client.forum.views.user_profile', args=[course_id, user_id])

def url_for_tags(course_id, tags):
    return reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id]) + '?' + urllib.urlencode({'tags': ",".join(tags)})

def render_content(content):
    return render_to_string('discussion/_content.html', {'content': content})
