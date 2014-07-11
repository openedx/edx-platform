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
import django.utils
from django.utils.translation import ugettext as _
from lxml import html, etree

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.html_module import CourseInfoModule

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
        course_updates = modulestore().create_item(user_id, location)

    course_update_items = get_course_update_items(course_updates, provided_id)
    return _get_visible_update(course_update_items)


def update_course_updates(location, update, passed_id=None, user=None):
    """
    Either add or update the given course update. It will add it if the passed_id is absent or None. It will update it if
    it has an passed_id which has a valid value. Until updates have distinct values, the passed_id is the location url + an index
    into the html structure.
    """
    try:
        course_updates = modulestore().get_item(location)
    except ItemNotFoundError:
        course_updates = modulestore().create_item(user.id, location)

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

    # update db record
    save_course_update_items(location, course_updates, course_update_items, user)
    # remove status key
    if "status" in course_update_dict:
        del course_update_dict["status"]
    return course_update_dict


def _course_info_content(html_parsed):
    """
    Constructs the HTML for the course info update, not including the header.
    """
    if len(html_parsed) == 1:
        # could enforce that update[0].tag == 'h2'
        content = html_parsed[0].tail
    else:
        content = html_parsed[0].tail if html_parsed[0].tail is not None else ""
        content += "\n".join([html.tostring(ele) for ele in html_parsed[1:]])
    return content


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


def get_course_update_items(course_updates, provided_id=None):
    """
    Returns list of course_updates data dictionaries either from new format if available or
    from old. This function don't modify old data to new data (in db), instead returns data
    in common old dictionary format.
    New Format: {"items" : [{"id": computed_id, "date": date, "content": html-string}],
                 "data": "<ol>[<li><h2>date</h2>content</li>]</ol>"}
    Old Format: {"data": "<ol>[<li><h2>date</h2>content</li>]</ol>"}
    """
    if course_updates and getattr(course_updates, "items", None):
        provided_id = _get_index(provided_id)
        if provided_id and 0 < provided_id <= len(course_updates.items):
            return course_updates.items[provided_id - 1]

        # return list in reversed order (old format: [4,3,2,1]) for compatibility
        return list(reversed(course_updates.items))
    else:
        # old method to get course updates
        # purely to handle free formed updates not done via editor. Actually kills them, but at least doesn't break.
        try:
            course_html_parsed = html.fromstring(course_updates.data)
        except (etree.XMLSyntaxError, etree.ParserError):
            log.error("Cannot parse: " + course_updates.data)
            escaped = django.utils.html.escape(course_updates.data)
            course_html_parsed = html.fromstring("<ol><li>" + escaped + "</li></ol>")

        # confirm that root is <ol>, iterate over <li>, pull out <h2> subs and then rest of val
        course_update_items = []
        provided_id = _get_index(provided_id)
        if course_html_parsed.tag == 'ol':
            # 0 is the newest
            for index, update in enumerate(course_html_parsed):
                if len(update) > 0:
                    content = _course_info_content(update)
                    # make the id on the client be 1..len w/ 1 being the oldest and len being the newest
                    computed_id = len(course_html_parsed) - index
                    payload = {
                        "id": computed_id,
                        "date": update.findtext("h2"),
                        "content": content
                    }
                    if provided_id == 0:
                        course_update_items.append(payload)
                    elif provided_id == computed_id:
                        return payload

        return course_update_items


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
