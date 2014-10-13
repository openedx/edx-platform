import pytz
from collections import defaultdict
import logging
from datetime import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import connection
from django.http import HttpResponse
from django.utils import simplejson
from django_comment_common.models import Role, FORUM_ROLE_STUDENT
from django_comment_client.permissions import check_permissions_by_view, cached_has_permission

from edxmako import lookup_template
import pystache_custom as pystache

from course_groups.cohorts import get_cohort_by_id, get_cohort_id, is_commentable_cohorted
from course_groups.models import CourseUserGroup
from xmodule.modulestore.django import modulestore
from django.utils.timezone import UTC
from opaque_keys.edx.locations import i4xEncoder
from opaque_keys.edx.keys import CourseKey
import json

log = logging.getLogger(__name__)


def extract(dic, keys):
    return {k: dic.get(k) for k in keys}


def strip_none(dic):
    return dict([(k, v) for k, v in dic.iteritems() if v is not None])


def strip_blank(dic):
    def _is_blank(v):
        return isinstance(v, str) and len(v.strip()) == 0
    return dict([(k, v) for k, v in dic.iteritems() if not _is_blank(v)])

# TODO should we be checking if d1 and d2 have the same keys with different values?


def merge_dict(dic1, dic2):
    return dict(dic1.items() + dic2.items())


def get_role_ids(course_id):
    roles = Role.objects.filter(course_id=course_id).exclude(name=FORUM_ROLE_STUDENT)
    return dict([(role.name, list(role.users.values_list('id', flat=True))) for role in roles])


def has_forum_access(uname, course_id, rolename):
    try:
        role = Role.objects.get(name=rolename, course_id=course_id)
    except Role.DoesNotExist:
        return False
    return role.users.filter(username=uname).exists()


def _get_discussion_modules(course):
    all_modules = modulestore().get_items(course.id, qualifiers={'category': 'discussion'})

    def has_required_keys(module):
        for key in ('discussion_id', 'discussion_category', 'discussion_target'):
            if getattr(module, key) is None:
                log.warning("Required key '%s' not in discussion %s, leaving out of category map" % (key, module.location))
                return False
        return True

    return filter(has_required_keys, all_modules)


def _get_discussion_id_map(course):
    def get_entry(module):
        discussion_id = module.discussion_id
        title = module.discussion_target
        last_category = module.discussion_category.split("/")[-1].strip()
        return (discussion_id, {"location": module.location, "title": last_category + " / " + title})

    return dict(map(get_entry, _get_discussion_modules(course)))


def _filter_unstarted_categories(category_map):

    now = datetime.now(UTC())

    result_map = {}

    unfiltered_queue = [category_map]
    filtered_queue = [result_map]

    while len(unfiltered_queue) > 0:

        unfiltered_map = unfiltered_queue.pop()
        filtered_map = filtered_queue.pop()

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
                    log.debug(u"Filtering out:%s with start_date: %s", child, unfiltered_map["entries"][child]["start_date"])
            else:
                if unfiltered_map["subcategories"][child]["start_date"] < now:
                    filtered_map["children"].append(child)
                    filtered_map["subcategories"][child] = {}
                    unfiltered_queue.append(unfiltered_map["subcategories"][child])
                    filtered_queue.append(filtered_map["subcategories"][child])

    return result_map


def _sort_map_entries(category_map, sort_alpha):
    things = []
    for title, entry in category_map["entries"].items():
        if entry["sort_key"] == None and sort_alpha:
            entry["sort_key"] = title
        things.append((title, entry))
    for title, category in category_map["subcategories"].items():
        things.append((title, category))
        _sort_map_entries(category_map["subcategories"][title], sort_alpha)
    category_map["children"] = [x[0] for x in sorted(things, key=lambda x: x[1]["sort_key"])]


def get_discussion_category_map(course):
    course_id = course.id

    unexpanded_category_map = defaultdict(list)

    modules = _get_discussion_modules(course)

    is_course_cohorted = course.is_cohorted
    cohorted_discussion_ids = course.cohorted_discussions

    for module in modules:
        id = module.discussion_id
        title = module.discussion_target
        sort_key = module.sort_key
        category = " / ".join([x.strip() for x in module.discussion_category.split("/")])
        #Handle case where module.start is None
        entry_start_date = module.start if module.start else datetime.max.replace(tzinfo=pytz.UTC)
        unexpanded_category_map[category].append({"title": title, "id": id, "sort_key": sort_key, "start_date": entry_start_date})

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
                                                      "start_date": entry["start_date"],
                                                      "is_cohorted": is_course_cohorted}

    # TODO.  BUG! : course location is not unique across multiple course runs!
    # (I think Kevin already noticed this)  Need to send course_id with requests, store it
    # in the backend.
    for topic, entry in course.discussion_topics.items():
        category_map['entries'][topic] = {"id": entry["id"],
                                          "sort_key": entry.get("sort_key", topic),
                                          "start_date": datetime.now(UTC()),
                                          "is_cohorted": is_course_cohorted and entry["id"] in cohorted_discussion_ids}

    _sort_map_entries(category_map, course.discussion_sort_alpha)

    return _filter_unstarted_categories(category_map)


class JsonResponse(HttpResponse):
    def __init__(self, data=None):
        content = json.dumps(data, cls=i4xEncoder)
        super(JsonResponse, self).__init__(content,
                                           mimetype='application/json; charset=utf-8')


class JsonError(HttpResponse):
    def __init__(self, error_messages=[], status=400):
        if isinstance(error_messages, basestring):
            error_messages = [error_messages]
        content = simplejson.dumps({'errors': error_messages},
                                   indent=2,
                                   ensure_ascii=False)
        super(JsonError, self).__init__(content,
                                        mimetype='application/json; charset=utf-8', status=status)


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

            log.info('%s queries run, total %s seconds' % (len(connection.queries), total_time))
        return response


def get_ability(course_id, content, user):
    return {
        'editable': check_permissions_by_view(user, course_id, content, "update_thread" if content['type'] == 'thread' else "update_comment"),
        'can_reply': check_permissions_by_view(user, course_id, content, "create_comment" if content['type'] == 'thread' else "create_sub_comment"),
        'can_delete': check_permissions_by_view(user, course_id, content, "delete_thread" if content['type'] == 'thread' else "delete_comment"),
        'can_openclose': check_permissions_by_view(user, course_id, content, "openclose_thread") if content['type'] == 'thread' else False,
        'can_vote': check_permissions_by_view(user, course_id, content, "vote_for_thread" if content['type'] == 'thread' else "vote_for_comment"),
    }

# TODO: RENAME


def get_annotated_content_info(course_id, content, user, user_info):
    """
    Get metadata for an individual content (thread or comment)
    """
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

# TODO: RENAME


def get_annotated_content_infos(course_id, thread, user, user_info):
    """
    Get metadata for a thread and its children
    """
    infos = {}

    def annotate(content):
        infos[str(content['id'])] = get_annotated_content_info(course_id, content, user, user_info)
        for child in (
                content.get('children', []) +
                content.get('endorsed_responses', []) +
                content.get('non_endorsed_responses', [])
        ):
            annotate(child)
    annotate(thread)
    return infos


def get_metadata_for_threads(course_id, threads, user, user_info):
    def infogetter(thread):
        return get_annotated_content_infos(course_id, thread, user, user_info)

    metadata = reduce(merge_dict, map(infogetter, threads), {})
    return metadata

# put this method in utils.py to avoid circular import dependency between helpers and mustache_helpers


def render_mustache(template_name, dictionary, *args, **kwargs):
    template = lookup_template('main', template_name).source
    return pystache.render(template, dictionary)


def permalink(content):
    if isinstance(content['course_id'], CourseKey):
        course_id = content['course_id'].to_deprecated_string()
    else:
        course_id = content['course_id']
    if content['type'] == 'thread':
        return reverse('django_comment_client.forum.views.single_thread',
                       args=[course_id, content['commentable_id'], content['id']])
    else:
        return reverse('django_comment_client.forum.views.single_thread',
                       args=[course_id, content['commentable_id'], content['thread_id']]) + '#' + content['id']


def extend_content(content):
    roles = {}
    if content.get('user_id'):
        try:
            user = User.objects.get(pk=content['user_id'])
            roles = dict(('name', role.name.lower()) for role in user.roles.filter(course_id=content['course_id']))
        except User.DoesNotExist:
            log.error('User ID {0} in comment content {1} but not in our DB.'.format(content.get('user_id'), content.get('id')))

    content_info = {
        'displayed_title': content.get('highlighted_title') or content.get('title', ''),
        'displayed_body': content.get('highlighted_body') or content.get('body', ''),
        'permalink': permalink(content),
        'roles': roles,
        'updated': content['created_at'] != content['updated_at'],
    }
    return merge_dict(content, content_info)


def add_courseware_context(content_list, course):
    id_map = _get_discussion_id_map(course)

    for content in content_list:
        commentable_id = content['commentable_id']
        if commentable_id in id_map:
            location = id_map[commentable_id]["location"].to_deprecated_string()
            title = id_map[commentable_id]["title"]

            url = reverse('jump_to', kwargs={"course_id": course.id.to_deprecated_string(),
                          "location": location})

            content.update({"courseware_url": url, "courseware_title": title})


def prepare_content(content, course_key, is_staff=False):
    """
    This function is used to pre-process thread and comment models in various
    ways before adding them to the HTTP response.  This includes fixing empty
    attribute fields, enforcing author anonymity, and enriching metadata around
    group ownership and response endorsement.

    @TODO: not all response pre-processing steps are currently integrated into
    this function.
    """
    fields = [
        'id', 'title', 'body', 'course_id', 'anonymous', 'anonymous_to_peers',
        'endorsed', 'parent_id', 'thread_id', 'votes', 'closed', 'created_at',
        'updated_at', 'depth', 'type', 'commentable_id', 'comments_count',
        'at_position_list', 'children', 'highlighted_title', 'highlighted_body',
        'courseware_title', 'courseware_url', 'unread_comments_count',
        'read', 'group_id', 'group_name', 'pinned', 'abuse_flaggers',
        'stats', 'resp_skip', 'resp_limit', 'resp_total', 'thread_type',
        'endorsed_responses', 'non_endorsed_responses', 'non_endorsed_resp_total',
        'endorsement',
    ]

    if (content.get('anonymous') is False) and ((content.get('anonymous_to_peers') is False) or is_staff):
        fields += ['username', 'user_id']

    content = strip_none(extract(content, fields))

    if content.get("endorsement"):
        endorsement = content["endorsement"]
        endorser = None
        if endorsement["user_id"]:
            try:
                endorser = User.objects.get(pk=endorsement["user_id"])
            except User.DoesNotExist:
                log.error("User ID {0} in endorsement for comment {1} but not in our DB.".format(
                    content.get('user_id'),
                    content.get('id'))
                )

        # Only reveal endorser if requester can see author or if endorser is staff
        if (
            endorser and
            ("username" in fields or cached_has_permission(endorser, "endorse_comment", course_id))
        ):
            endorsement["username"] = endorser.username
        else:
            del endorsement["user_id"]

    for child_content_key in ["children", "endorsed_responses", "non_endorsed_responses"]:
        if child_content_key in content:
            children = [
                prepare_content(child, course_key, is_staff) for child in content[child_content_key]
            ]
            content[child_content_key] = children

    # Augment the specified thread info to include the group name if a group id is present.
    if content.get('group_id') is not None:
        content['group_name'] = get_cohort_by_id(course_key, content.get('group_id')).name

    return content


def get_group_id_for_comments_service(request, course_key, commentable_id=None):
    """
    Given a user requesting content within a `commentable_id`, determine the
    group_id which should be passed to the comments service.

    Returns:
        int: the group_id to pass to the comments service or None if nothing
        should be passed

    Raises:
        ValueError if the requested group_id is invalid
    """
    if commentable_id is None or is_commentable_cohorted(course_key, commentable_id):
        if request.method == "GET":
            requested_group_id = request.GET.get('group_id')
        elif request.method == "POST":
            requested_group_id = request.POST.get('group_id')
        if cached_has_permission(request.user, "see_all_cohorts", course_key):
            if not requested_group_id:
                return None
            try:
                group_id = int(requested_group_id)
                get_cohort_by_id(course_key, group_id)
            except CourseUserGroup.DoesNotExist:
                raise ValueError
        else:
            # regular users always query with their own id.
            group_id = get_cohort_id(request.user, course_key)
        return group_id
    else:
        # Never pass a group_id to the comments service for a non-cohorted
        # commentable
        return None
