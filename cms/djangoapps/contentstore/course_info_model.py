"""
Views for viewing, adding, updating and deleting course updates.

Current db representation:
{
    "_id" : locationjson,
    "definition" : {
        "data" : "<ol>[<li><h2>date</h2>content</li>]</ol>"},
        "items" : [{"id": ID, "date": DATE, "content": CONTENT}]
        "metadata" : ignored
    }
}
"""

import re
import logging

from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.html_module import CourseInfoModule

from openedx.core.lib.xblock_utils import get_course_update_items
from cms.djangoapps.contentstore.push_notification import enqueue_push_course_update

# # This should be in a class which inherits from XmlDescriptor
log = logging.getLogger(__name__)


def get_course_updates(location, provided_id, user_id):
    """
    Retrieve the relevant course_info updates and unpack into the model which the client expects:
    [{id : index, date : string, content : html string}]
    """
    try:
        course_updates = modulestore().get_item(location)
    except ItemNotFoundError:
        course_updates = modulestore().create_item(user_id, location.course_key, location.block_type, location.block_id)

    course_update_items = get_course_update_items(course_updates, _get_index(provided_id))
    return _get_visible_update(course_update_items)


def update_course_updates(location, update, passed_id=None, user=None):
    """
    Either add or update the given course update.
    Add:
        If the passed_id is absent or None, the course update is added.
        If push_notification_selected is set in the update, a celery task for the push notification is created.
    Update:
        It will update it if it has a passed_id which has a valid value.
        Until updates have distinct values, the passed_id is the location url + an index into the html structure.
    """
    try:
        course_updates = modulestore().get_item(location)
    except ItemNotFoundError:
        course_updates = modulestore().create_item(user.id, location.course_key, location.block_type, location.block_id)

    course_update_items = list(reversed(get_course_update_items(course_updates)))

    if passed_id is not None:
        passed_index = _get_index(passed_id)
        # oldest update at start of list
        if 0 < passed_index <= len(course_update_items):
            course_update_dict = course_update_items[passed_index - 1]
            course_update_dict["date"] = update["date"]
            course_update_dict["content"] = update["content"]
            course_update_items[passed_index - 1] = course_update_dict
        else:
            return HttpResponseBadRequest(_("Invalid course update id."))
    else:
        course_update_dict = {
            "id": len(course_update_items) + 1,
            "date": update["date"],
            "content": update["content"],
            "status": CourseInfoModule.STATUS_VISIBLE
        }
        course_update_items.append(course_update_dict)
        enqueue_push_course_update(update, location.course_key)

    # update db record
    save_course_update_items(location, course_updates, course_update_items, user)
    # remove status key
    if "status" in course_update_dict:
        del course_update_dict["status"]
    return course_update_dict


def _make_update_dict(update):
    """
    Return course update item as a dictionary with required keys ('id', "date" and "content").
    """
    return {
        "id": update["id"],
        "date": update["date"],
        "content": update["content"],
    }


def _get_visible_update(course_update_items):
    """
    Filter course update items which have status "deleted".
    """
    if isinstance(course_update_items, dict):
        # single course update item
        if course_update_items.get("status") != CourseInfoModule.STATUS_DELETED:
            return _make_update_dict(course_update_items)
        else:
            # requested course update item has been deleted (soft delete)
            return {"error": _("Course update not found."), "status": 404}

    return ([_make_update_dict(update) for update in course_update_items
             if update.get("status") != CourseInfoModule.STATUS_DELETED])


# pylint: disable=unused-argument
def delete_course_update(location, update, passed_id, user):
    """
    Don't delete course update item from db.
    Delete the given course_info update by settings "status" flag to 'deleted'.
    Returns the resulting course_updates.
    """
    if not passed_id:
        return HttpResponseBadRequest()

    try:
        course_updates = modulestore().get_item(location)
    except ItemNotFoundError:
        return HttpResponseBadRequest()

    course_update_items = list(reversed(get_course_update_items(course_updates)))
    passed_index = _get_index(passed_id)

    # delete update item from given index
    if 0 < passed_index <= len(course_update_items):
        course_update_item = course_update_items[passed_index - 1]
        # soft delete course update item
        course_update_item["status"] = CourseInfoModule.STATUS_DELETED
        course_update_items[passed_index - 1] = course_update_item

        # update db record
        save_course_update_items(location, course_updates, course_update_items, user)
        return _get_visible_update(course_update_items)
    else:
        return HttpResponseBadRequest(_("Invalid course update id."))


def _get_index(passed_id=None):
    """
    From the url w/ index appended, get the index.
    """
    if passed_id:
        index_matcher = re.search(r'.*?/?(\d+)$', passed_id)
        if index_matcher:
            return int(index_matcher.group(1))

    # return 0 if no index found
    return 0


def _get_html(course_updates_items):
    """
    Method to create course_updates_html from course_updates items
    """
    list_items = []
    for update in reversed(course_updates_items):
        # filter course update items which have status "deleted".
        if update.get("status") != CourseInfoModule.STATUS_DELETED:
            list_items.append(u"<article><h2>{date}</h2>{content}</article>".format(**update))
    return u"<section>{list_items}</section>".format(list_items="".join(list_items))


def save_course_update_items(location, course_updates, course_update_items, user=None):
    """
    Save list of course_updates data dictionaries in new field ("course_updates.items")
    and html related to course update in 'data' ("course_updates.data") field.
    """
    course_updates.items = course_update_items
    course_updates.data = _get_html(course_update_items)

    # update db record
    modulestore().update_item(course_updates, user.id)

    return course_updates
