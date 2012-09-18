import time
from collections import defaultdict
from importlib import import_module

from courseware.models import StudentModuleCache
from courseware.module_render import get_module
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import path_to_location
from django.http import HttpResponse
from django.utils import simplejson
from django.db import connection
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django_comment_client.permissions import check_permissions_by_view
from django_comment_client.models import Role
from mitxmako import middleware

import logging
import operator
import itertools
import urllib
import pystache_custom as pystache


# TODO these should be cached via django's caching rather than in-memory globals
_FULLMODULES = None
_DISCUSSIONINFO = defaultdict(dict)

def extract(dic, keys):
    return {k: dic.get(k) for k in keys}

def strip_none(dic):
    return dict([(k, v) for k, v in dic.iteritems() if v is not None])

def strip_blank(dic):
    def _is_blank(v):
        return isinstance(v, str) and len(v.strip()) == 0
    return dict([(k, v) for k, v in dic.iteritems() if not _is_blank(v)])

def merge_dict(dic1, dic2):
    return dict(dic1.items() + dic2.items())

def get_role_ids(course_id):
    roles = Role.objects.filter(course_id=course_id)
    staff = list(User.objects.filter(is_staff=True).values_list('id', flat=True))
    roles_with_ids = {'Staff': staff}
    for role in roles:
      roles_with_ids[role.name] = list(role.users.values_list('id', flat=True))
    return roles_with_ids

def get_full_modules():
    global _FULLMODULES
    if not _FULLMODULES:
        _FULLMODULES = modulestore().modules
    return _FULLMODULES

def get_discussion_id_map(course):
    """
        return a dict of the form {category: modules}
    """
    global _DISCUSSIONINFO
    if not _DISCUSSIONINFO[course.id]:
        initialize_discussion_info(course)
    return _DISCUSSIONINFO[course.id]['id_map']

def get_discussion_title(course, discussion_id):
    global _DISCUSSIONINFO
    if not _DISCUSSIONINFO[course.id]:
        initialize_discussion_info(course)
    title = _DISCUSSIONINFO[course.id]['id_map'].get(discussion_id, {}).get('title', '(no title)')
    return title

def get_discussion_category_map(course):

    global _DISCUSSIONINFO
    if not _DISCUSSIONINFO[course.id]:
        initialize_discussion_info(course)
    return filter_unstarted_categories(_DISCUSSIONINFO[course.id]['category_map'])

def filter_unstarted_categories(category_map):

    now = time.gmtime()

    result_map = {}

    unfiltered_queue = [category_map]
    filtered_queue   = [result_map]

    while len(unfiltered_queue) > 0:

        unfiltered_map = unfiltered_queue.pop()
        filtered_map   = filtered_queue.pop()

        filtered_map["children"] = []
        filtered_map["entries"] = {}
        filtered_map["subcategories"] = {}

        for child in unfiltered_map["children"]:
            if child in unfiltered_map["entries"]:
                if unfiltered_map["entries"][child]["start_date"] <= now:
                    filtered_map["children"].append(child)
                    filtered_map["entries"][child] = {}
                    for key in unfiltered_map["entries"][child]:
                        if key != "start_date":
                            filtered_map["entries"][child][key] = unfiltered_map["entries"][child][key]
                else:
                    print "filtering %s" % child, unfiltered_map["entries"][child]["start_date"]
            else:
                if unfiltered_map["subcategories"][child]["start_date"] < now:
                    filtered_map["children"].append(child)
                    filtered_map["subcategories"][child] = {}
                    unfiltered_queue.append(unfiltered_map["subcategories"][child])
                    filtered_queue.append(filtered_map["subcategories"][child])

    return result_map

def sort_map_entries(category_map):
    things = []
    for title, entry in category_map["entries"].items():
        things.append((title, entry))
    for title, category in category_map["subcategories"].items():
        things.append((title, category))
        sort_map_entries(category_map["subcategories"][title])
    category_map["children"] = [x[0] for x in sorted(things, key=lambda x: x[1]["sort_key"])]

def initialize_discussion_info(course):

    global _DISCUSSIONINFO
    if _DISCUSSIONINFO[course.id]:
        return

    course_id = course.id
    url_course_id = course_id.replace('/', '_').replace('.', '_')

    all_modules = get_full_modules()[course_id]

    discussion_id_map = {}

    unexpanded_category_map = defaultdict(list)

    for location, module in all_modules.items():
        if location.category == 'discussion':
            id = module.metadata['id']
            category = module.metadata['discussion_category']
            title = module.metadata['for']
            sort_key = module.metadata.get('sort_key', title)
            category = " / ".join([x.strip() for x in category.split("/")])
            last_category = category.split("/")[-1]
            discussion_id_map[id] = {"location": location, "title": last_category + " / " + title}
            unexpanded_category_map[category].append({"title": title, "id": id,
                "sort_key": sort_key, "start_date": module.start})

    category_map = {"entries": defaultdict(dict), "subcategories": defaultdict(dict)}
    for category_path, entries in unexpanded_category_map.items():
        node = category_map["subcategories"]
        path = [x.strip() for x in category_path.split("/")]

        # Find the earliest start date for the entries in this category
        category_start_date = None
        for entry in entries:
            if category_start_date is None or entry["start_date"] < category_start_date:
                category_start_date = entry["start_date"]

        for level in path[:-1]:
            if level not in node:
                node[level] = {"subcategories": defaultdict(dict),
                               "entries": defaultdict(dict),
                               "sort_key": level,
                               "start_date": category_start_date}
            else:
                if node[level]["start_date"] > category_start_date:
                    node[level]["start_date"] = category_start_date
            node = node[level]["subcategories"]

        level = path[-1]
        if level not in node:
            node[level] = {"subcategories": defaultdict(dict),
                            "entries": defaultdict(dict),
                            "sort_key": level,
                            "start_date": category_start_date}
        else:
            if node[level]["start_date"] > category_start_date:
                node[level]["start_date"] = category_start_date

        for entry in entries:
            node[level]["entries"][entry["title"]] = {"id": entry["id"],
                                                      "sort_key": entry["sort_key"],
                                                      "start_date": entry["start_date"]}

    default_topics = {'General': {'id' :course.location.html_id()}}
    discussion_topics = course.metadata.get('discussion_topics', default_topics)
    for topic, entry in discussion_topics.items():
        category_map['entries'][topic] = {"id": entry["id"],
                                          "sort_key": entry.get("sort_key", topic),
                                          "start_date": time.gmtime()}
    sort_map_entries(category_map)

    _DISCUSSIONINFO[course.id]['id_map'] = discussion_id_map
    _DISCUSSIONINFO[course.id]['category_map'] = category_map

class JsonResponse(HttpResponse):
    def __init__(self, data=None):
        content = simplejson.dumps(data)
        super(JsonResponse, self).__init__(content,
                                           mimetype='application/json; charset=utf8')

class JsonError(HttpResponse):
    def __init__(self, error_messages=[], status=400):
        if isinstance(error_messages, str):
            error_messages = [error_messages]
        content = simplejson.dumps({'errors': error_messages},
                                   indent=2,
                                   ensure_ascii=False)
        super(JsonError, self).__init__(content,
                                        mimetype='application/json; charset=utf8', status=status)

class HtmlResponse(HttpResponse):
    def __init__(self, html=''):
        super(HtmlResponse, self).__init__(html, content_type='text/plain')

class ViewNameMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.view_name = view_func.__name__

class QueryCountDebugMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """
    def process_response(self, request, response):
        if response.status_code == 200:
            total_time = 0

            for query in connection.queries:
                query_time = query.get('time')
                if query_time is None:
                    # django-debug-toolbar monkeypatches the connection
                    # cursor wrapper and adds extra information in each
                    # item in connection.queries. The query time is stored
                    # under the key "duration" rather than "time" and is
                    # in milliseconds, not seconds.
                    query_time = query.get('duration', 0) / 1000
                total_time += float(query_time)

            logging.info('%s queries run, total %s seconds' % (len(connection.queries), total_time))
        return response

def get_ability(course_id, content, user):
    return {
            'editable': check_permissions_by_view(user, course_id, content, "update_thread" if content['type'] == 'thread' else "update_comment"),
            'can_reply': check_permissions_by_view(user, course_id, content, "create_comment" if content['type'] == 'thread' else "create_sub_comment"),
            'can_endorse': check_permissions_by_view(user, course_id, content, "endorse_comment") if content['type'] == 'comment' else False,
            'can_delete': check_permissions_by_view(user, course_id, content, "delete_thread" if content['type'] == 'thread' else "delete_comment"),
            'can_openclose': check_permissions_by_view(user, course_id, content, "openclose_thread") if content['type'] == 'thread' else False,
            'can_vote': check_permissions_by_view(user, course_id, content, "vote_for_thread" if content['type'] == 'thread' else "vote_for_comment"),
    }

def get_annotated_content_info(course_id, content, user, user_info):
    voted = ''
    if content['id'] in user_info['upvoted_ids']:
        voted = 'up'
    elif content['id'] in user_info['downvoted_ids']:
        voted = 'down'
    return {
        'voted': voted,
        'subscribed': content['id'] in user_info['subscribed_thread_ids'],
        'ability': get_ability(course_id, content, user),
    }

def get_annotated_content_infos(course_id, thread, user, user_info):
    infos = {}
    def annotate(content):
        infos[str(content['id'])] = get_annotated_content_info(course_id, content, user, user_info)
        for child in content.get('children', []):
            annotate(child)
    annotate(thread)
    return infos

# put this method in utils.py to avoid circular import dependency between helpers and mustache_helpers
def url_for_tags(course_id, tags):
    return reverse('django_comment_client.forum.views.forum_form_discussion', args=[course_id]) + '?' + urllib.urlencode({'tags': tags})

def render_mustache(template_name, dictionary, *args, **kwargs):
    template = middleware.lookup['main'].get_template(template_name).source
    return pystache.render(template, dictionary)

def permalink(content):
    if content['type'] == 'thread':
        return reverse('django_comment_client.forum.views.single_thread',
                       args=[content['course_id'], content['commentable_id'], content['id']])
    else:
        return reverse('django_comment_client.forum.views.single_thread',
                       args=[content['course_id'], content['commentable_id'], content['thread_id']]) + '#' + content['id']

def extend_content(content):
    roles = {}
    if content.get('user_id'):
        try:
            user = User.objects.get(pk=content['user_id'])
            roles = dict(('name', role.name.lower()) for role in user.roles.filter(course_id=content['course_id']))
        except user.DoesNotExist:
            logging.error('User ID {0} in comment content {1} but not in our DB.'.format(content.get('user_id'), content.get('id')))
        
    content_info = {
        'displayed_title': content.get('highlighted_title') or content.get('title', ''),
        'displayed_body': content.get('highlighted_body') or content.get('body', ''),
        'raw_tags': ','.join(content.get('tags', [])),
        'permalink': permalink(content),
        'roles': roles,
        'updated': content['created_at']!=content['updated_at'],
    }
    return merge_dict(content, content_info)

def get_courseware_context(content, course):
    id_map = get_discussion_id_map(course)
    id = content['commentable_id']
    content_info = None
    if id in id_map:
        location = id_map[id]["location"].url()
        title = id_map[id]["title"]
        (course_id, chapter, section, position) = path_to_location(modulestore(), course.id, location)
        url = reverse('courseware_position', kwargs={"course_id":course_id, 
                                                     "chapter":chapter, 
                                                     "section":section, 
                                                     "position":position})
        content_info = {"courseware_url": url, "courseware_title": title}
    return content_info

def safe_content(content):
    fields = [
        'id', 'title', 'body', 'course_id', 'anonymous', 'anonymous_to_peers',
        'endorsed', 'parent_id', 'thread_id', 'votes', 'closed', 'created_at',
        'updated_at', 'depth', 'type', 'commentable_id', 'comments_count',
        'at_position_list', 'children', 'highlighted_title', 'highlighted_body',
        'courseware_title', 'courseware_url', 'tags', 'unread_comments_count',
        'viewed',
    ]

    if (content.get('anonymous') is False) and (content.get('anonymous_to_peers') is False):
        fields += ['username', 'user_id']

    if 'children' in content:
        safe_children = [safe_content(child) for child in content['children']]
        content['children'] = safe_children

    return strip_none(extract(content, fields))
