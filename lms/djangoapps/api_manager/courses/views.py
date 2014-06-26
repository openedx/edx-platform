""" API implementation for course-oriented interactions. """

from collections import OrderedDict
import logging
import itertools
from lxml import etree
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Sum, Count
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.response import Response

from api_manager.models import CourseGroupRelationship, CourseContentGroupRelationship, GroupProfile, \
    CourseModuleCompletion
from api_manager.permissions import SecureAPIView, SecureListAPIView
from api_manager.users.serializers import UserSerializer
from courseware import module_render
from courseware.courses import get_course, get_course_about_section, get_course_info_section
from courseware.model_data import FieldDataCache
from courseware.models import StudentModule
from courseware.views import get_static_tab_contents
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location, InvalidLocationError
from api_manager.permissions import SecureAPIView, SecureListAPIView
from api_manager.utils import generate_base_uri
from projects.models import Project
from projects.serializers import ProjectSerializer

from .serializers import CourseModuleCompletionSerializer
from .serializers import GradeSerializer, CourseLeadersSerializer, CourseCompletionsLeadersSerializer

log = logging.getLogger(__name__)

def _get_content_children(content, content_type=None):
    """
    Parses the provided content object looking for children
    Matches on child content type (category) when specified
    """
    children = []
    if hasattr(content, 'children'):
        child_content = content.get_children()
        for child in child_content:
            if content_type:
                if getattr(child, 'category') == content_type:
                    children.append(child)
            else:
                children.append(child)
    return children


def _serialize_content(request, course_id, content):
    """
    Loads the specified content object into the response dict
    This should probably evolve to use DRF serializers
    """
    data = {}

    if getattr(content, 'id') == course_id:
        content_id = content.id
    else:
        content_id = content.location.url()
    data['id'] = content_id

    if hasattr(content, 'display_name'):
        data['name'] = content.display_name

    data['category'] = content.location.category

    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    content_uri = '{}://{}/api/courses/{}'.format(
        protocol,
        request.get_host(),
        course_id.encode('utf-8')
    )

    # Some things we do only if the content object is a course
    if (course_id == content_id):
        data['number'] = content.location.course
        data['org'] = content.location.org

    # Other things we do only if the content object is not a course
    else:
        content_uri = '{}/content/{}'.format(content_uri, content_id)
    data['uri'] = content_uri

    if hasattr(content, 'due'):
        data['due'] = content.due

    data['start'] = getattr(content, 'start', None)
    data['end'] = getattr(content, 'end', None)

    return data


def _serialize_content_children(request, course_id, children):
    """
    Loads the specified content child data into the response dict
    This should probably evolve to use DRF serializers
    """
    data = []
    if children:
        for child in children:
            child_data = _serialize_content(
                request,
                course_id,
                child
            )
            data.append(child_data)
    return data


def _serialize_content_with_children(request, course_descriptor, descriptor, depth):
    data = _serialize_content(
        request,
        course_descriptor.id,
        descriptor
    )
    if depth > 0:
        data['children'] = []
        for child in descriptor.get_children():
            data['children'].append(_serialize_content_with_children(
                request,
                course_descriptor,
                child,
                depth - 1
            ))
    return data


def _inner_content(tag):
    """
    Helper method
    """
    inner_content = None
    if tag is not None:
        inner_content = tag.text if tag.text else u''
        inner_content += u''.join(etree.tostring(e) for e in tag)
        inner_content += tag.tail if tag.tail else u''

    return inner_content


def _parse_overview_html(html):
    """
    Helper method to break up the course about HTML into components
    Overview content is stored in MongoDB (aka, the module store) with the following naming convention

            {
                "_id.org":"i4x",
                "_id.course":<course_num>,
                "_id.category":"about",
                "_id.name":"overview"
            }
    """
    result = {}

    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(html), parser)

    sections = tree.findall('/body/section')

    result = []
    for section in sections:
        section_class = section.get('class')
        if section_class:
            section_data = OrderedDict()
            section_data['class'] = section_class

            section_data['attributes'] = {}
            for attribute_key in section.keys():
                # don't return the class attribute as we are already using the class attribute
                # as a key name to the result set, so we don't want to end up duplicating it
                if attribute_key != 'class':
                    section_data['attributes'][attribute_key] = section.get(attribute_key)

            articles = section.findall('article')
            if articles:
                section_data['articles'] = []
                for article in articles:
                    article_class = article.get('class')
                    if article_class:
                        article_data = OrderedDict()
                        article_data['class'] = article_class

                        if article_class == "teacher":

                            name_element = article.find('h3')
                            if name_element is not None:
                                article_data['name'] = name_element.text

                            image_element = article.find("./div[@class='teacher-image']/img")
                            if image_element is not None:
                                article_data['image_src'] = image_element.get('src')

                            bios = article.findall('p')
                            bio_html = ''
                            for bio in bios:
                                bio_html += etree.tostring(bio)

                            if bio_html:
                                article_data['bio'] = bio_html
                        else:
                            article_data['body'] = _inner_content(article)

                        section_data['articles'].append(article_data)
            else:
                section_data['body'] = _inner_content(section)

            result.append(section_data)

    return result


def _parse_updates_html(html):
    """
    Helper method to extract updates contained within the course info HTML into components
    Updates content is stored in MongoDB (aka, the module store) with the following naming convention

            {
                "_id.org":"i4x",
                "_id.course":<course_num>,
                "_id.category":"course_info",
                "_id.name":"updates"
            }
    """
    result = {}

    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(html), parser)

    # get all of the individual postings
    postings = tree.findall('/body/section/article')

    # be backwards compatible
    if not postings:
        postings = tree.findall('/body/ol/li')

    result = []
    for posting in postings:
        posting_data = {}
        posting_date_element = posting.find('h2')
        if posting_date_element is not None:
            posting_data['date'] = posting_date_element.text

        content = u''
        for el in posting:
            # note, we can't delete or skip over the date element in
            # the HTML tree because there might be some tailing content
            if el != posting_date_element:
                content += etree.tostring(el)
            else:
                content += el.tail if el.tail else u''

        posting_data['content'] = content.strip()
        result.append(posting_data)

    return result


class CourseContentList(SecureAPIView):
    """
    **Use Case**

        CourseContentList gets a collection of content for a given
        course. You can use the **uri** value in
        the response to get details for that content entity.

        CourseContentList has an optional type parameter that allows you to
        filter the response by content type. The value of the type parameter
        matches the category value in the response. Valid values for the type
        parameter are:

        * chapter
        * sequential
        * vertical
        * html
        * problem
        * discussion
        * video
        * [CONFIRM]

    **Example requests**:

        GET /api/courses/{course_id}/content

        GET /api/courses/{course_id}/content?type=video

        GET /api/courses/{course_id}/content/{content_id}/children

    **Response Values**

        * category: The type of content.

        * due: The due date.

        * uri: The URI to use to get details of the content entity.

        * id: The unique identifier for the content entity.

        * name: The name of the course.
    """

    def get(self, request, course_id, content_id=None):
        if content_id is None:
            content_id = course_id
        response_data = []
        content_type = request.QUERY_PARAMS.get('type', None)
        store = modulestore()
        if course_id != content_id:
            try:
                content = store.get_instance(course_id, Location(content_id))
            except InvalidLocationError:
                content = None
        else:
            content = get_course(course_id)
        if content:
            children = _get_content_children(content, content_type)
            response_data = _serialize_content_children(
                request,
                course_id,
                children
            )
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)


class CourseContentDetail(SecureAPIView):
    """
    **Use Case**

        CourseContentDetail returns a JSON collection for a specified
        CourseContent entity. If the specified CourseContent is the Course, the
        course representation is returned. You can use the uri values in the
        children collection in the JSON response to get details for that content
        entity.

        CourseContentDetail has an optional type parameter that allows you to
        filter the response by content type. The value of the type parameter
        matches the category value in the response. Valid values for the type
        parameter are:

        * chapter
        * sequential
        * vertical
        * html
        * problem
        * discussion
        * video
        * [CONFIRM]

    **Example Request**

          GET /api/courses/{course_id}/content/{content_id}

    **Response Values**

        * category: The type of content.

        * name: The name of the content entity.

        * due:  The due date.

        * uri: The URI of the content entity.

        * id: The unique identifier for the course.

        * children: Content entities that this conent entity contains.

        * resources: A list of URIs to available users and groups:
          * Related Users  /api/courses/{course_id}/content/{content_id}/users
          * Related Groups /api/courses/{course_id}/content/{content_id}/groups
    """

    def get(self, request, course_id, content_id):
        store = modulestore()
        response_data = {}
        base_uri = generate_base_uri(request)
        content_type = request.QUERY_PARAMS.get('type', None)
        response_data['uri'] = base_uri
        if course_id != content_id:
            element_name = 'children'
            try:
                content = store.get_instance(course_id, Location(content_id))
            except InvalidLocationError:
                content = None
        else:
            element_name = 'content'
            content = get_course(course_id)
            protocol = 'http'
            if request.is_secure():
                protocol = protocol + 's'
            response_data['uri'] = '{}://{}/api/courses/{}'.format(
                protocol,
                request.get_host(),
                course_id.encode('utf-8')
            )
        if content:
            response_data = _serialize_content(
                request,
                course_id,
                content
            )
            children = _get_content_children(content, content_type)
            response_data[element_name] = _serialize_content_children(
                request,
                course_id,
                children
            )
            base_uri_without_qs = generate_base_uri(request, True)
            response_data['resources'] = []
            resource_uri = '{}/users'.format(base_uri_without_qs)
            response_data['resources'].append({'uri': resource_uri})
            resource_uri = '{}/groups'.format(base_uri_without_qs)
            response_data['resources'].append({'uri': resource_uri})
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)


class CoursesList(SecureAPIView):
    """
    **Use Case**

        CoursesList returns a collection of courses in the edX Platform. You can
        use the uri value in the response to get details of the course.

    **Example Request**

          GET /api/courses

    **Response Values**

        * category: The type of content. In this case, the value is always "course".

        * name: The name of the course.

        * uri: The URI to use to get details of the course.

        * number: The course number.

        * due:  The due date. For courses, the value is always null.

        * org: The organization specified for the course.

        * id: The unique identifier for the course.
    """

    def get(self, request):
        response_data = []
        store = modulestore()
        course_descriptors = store.get_courses()
        for course_descriptor in course_descriptors:
            course_data = _serialize_content(
                request,
                course_descriptor.id,
                course_descriptor
            )
            response_data.append(course_data)
        return Response(response_data, status=status.HTTP_200_OK)


class CoursesDetail(SecureAPIView):
    """
    **Use Case**

        CoursesDetail returns details for a course. You can use the uri values
        in the resources collection in the response to get more course
        information for:

        * Users (/api/courses/{course_id}/users/)
        * Groups (/api/courses/{course_id}/groups/)
        * Course Overview (/api/courses/{course_id}/overview/)
        * Course Updates (/api/courses/{course_id}/updates/)
        * Course Pages (/api/courses/{course_id}/static_tabs/)

        CoursesDetail has an optional **depth** parameter that allows you to
        get course content children to the specified tree level.

    **Example requests**:

        GET /api/courses/{course_id}

        GET /api/courses/{course_id}?depth=2

    **Response Values**

        * category: The type of content.

        * name: The name of the course.

        * uri: The URI to use to get details of the course.

        * number: The course number.

        * content: When the depth parameter is used, a collection of child
          course content entities, such as chapters, sequentials, and
          components.

        * due:  The due date. For courses, the value is always null.

        * org: The organization specified for the course.

        * id: The unique identifier for the course.

        * resources: A collection of URIs to use to get more information about
          the course.
    """

    def get(self, request, course_id):
        depth = request.QUERY_PARAMS.get('depth', 0)
        depth_int = int(depth)
        # get_course_by_id raises an Http404 if the requested course is invalid
        # Rather than catching it, we just let it bubble up
        try:
            course_descriptor = get_course(course_id, depth=depth_int)
        except ValueError:
            course_descriptor = None
        if not course_descriptor:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        if depth_int > 0:
            response_data = _serialize_content_with_children(
                request,
                course_descriptor,
                course_descriptor,  # Primer for recursive function
                depth_int
            )
            response_data['content'] = response_data['children']
            response_data.pop('children')
        else:
            response_data = _serialize_content(
                request,
                course_descriptor.id,
                course_descriptor
            )
        base_uri = generate_base_uri(request)
        response_data['uri'] = base_uri
        base_uri_without_qs = generate_base_uri(request, True)
        response_data['resources'] = []
        resource_uri = '{}/content/'.format(base_uri_without_qs)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/groups/'.format(base_uri_without_qs)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/overview/'.format(base_uri_without_qs)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/updates/'.format(base_uri_without_qs)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/static_tabs/'.format(base_uri_without_qs)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/users/'.format(base_uri_without_qs)
        response_data['resources'].append({'uri': resource_uri})
        return Response(response_data, status=status.HTTP_200_OK)

class CoursesGroupsList(SecureAPIView):
    """
    **Use Case**

        CoursesGroupsList returns a collection of course group relationship
        entities(?) for a specified course entity.

        CoursesGroupsList has an optional **type** parameter that allows you to
        filter the groups returned. Valid values for the type parameter are:

        * [CONFIRM]

    **Example Request**

        GET /api/courses/{course_id}/groups?type=workgroup

        POST /api/courses/{course_id}/groups

    **Response Values**


    ### The CoursesGroupsList view allows clients to retrieve a list of Groups for a given Course entity
    - URI: ```/api/courses/{course_id}/groups/```
    - GET: Returns a JSON representation (array) of the set of CourseGroupRelationship entities
        * type: Set filtering parameter
    - POST: Creates a new relationship between the provided Course and Group
        * group_id: __required__, The identifier for the Group with which we're establishing a relationship
    - POST Example:

            {
                "group_id" : 12345,
            }
    ### Use Cases/Notes:
    * Example: Display all of the courses for a particular academic series/program
    * If a relationship already exists between a Course and a particular group, the system returns 409 Conflict
    * The 'type' parameter filters groups by their 'group_type' field ('workgroup', 'series', etc.)
    """

    def post(self, request, course_id):
        """
        POST /api/courses/{course_id}/groups
        """
        response_data = {}
        group_id = request.DATA['group_id']
        base_uri = generate_base_uri(request)
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            existing_group = None
        if existing_course and existing_group:
            try:
                existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group)
            except ObjectDoesNotExist:
                existing_relationship = None
            if existing_relationship is None:
                CourseGroupRelationship.objects.create(course_id=course_id, group=existing_group)
                response_data['course_id'] = str(existing_course.id)
                response_data['group_id'] = str(existing_group.id)
                response_data['uri'] = '{}/{}'.format(base_uri, existing_group.id)
                response_status = status.HTTP_201_CREATED
            else:
                response_data['message'] = "Relationship already exists."
                response_status = status.HTTP_409_CONFLICT
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def get(self, request, course_id):
        """
        GET /api/courses/{course_id}/groups?type=workgroup
        """
        try:
            get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        group_type = request.QUERY_PARAMS.get('type', None)
        course_groups = CourseGroupRelationship.objects.filter(course_id=course_id)

        if group_type:
            course_groups = course_groups.filter(group__groupprofile__group_type=group_type)
        response_data = []
        for course_group in course_groups:
            group_profile = GroupProfile.objects.get(group_id=course_group.group_id)
            group_data = {'id': course_group.group_id, 'name': group_profile.name}
            response_data.append(group_data)
        response_status = status.HTTP_200_OK
        return Response(response_data, status=response_status)

class CoursesGroupsDetail(SecureAPIView):
    """
    ### The CoursesGroupsDetail view allows clients to interact with a specific CourseGroupRelationship entity
    - URI: ```/api/courses/{course_id}/group/{group_id}```
    - GET: Returns a JSON representation of the specified CourseGroupRelationship entity
        * type: Set filtering parameter
    - DELETE: Removes an existing CourseGroupRelationship from the system
    ### Use Cases/Notes:
    * Use this operation to confirm the existence of a specific Course-Group entity relationship
    """

    def get(self, request, course_id, group_id):
        """
        GET /api/courses/{course_id}/groups/{group_id}
        """
        try:
            existing_course = get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data = {}
        base_uri = generate_base_uri(request)
        response_data['uri'] = base_uri
        response_data['course_id'] = course_id
        response_data['group_id'] = group_id
        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, course_id, group_id):
        """
        DELETE /api/courses/{course_id}/groups/{group_id}
        """
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group).delete()
        except ObjectDoesNotExist:
            pass
        response_data = {}
        response_data['uri'] = generate_base_uri(request)
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


class CoursesOverview(SecureAPIView):
    """
    **Use Case**

        CoursesOverview returns an HTML representation of the overview for the
        specified course. CoursesOverview has an optional parse parameter that
        when true breaks the response into a collection named sections. By
        default, parse is false.

    **Example Request**

          GET /api/courses/{course_id}/overview

          GET /api/courses/{course_id}/overview?parse=true

    **Response Values**

        * overview_html: The HTML representation of the course overview.
          Sections of the overview are indicated by an HTML section element.

        * sections: When parse=true, a collection of JSON objects representing
          parts of the course overview.

    """

    def get(self, request, course_id):
        response_data = OrderedDict()
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if existing_course:
            existing_content = get_course_about_section(existing_course, 'overview')
            if existing_content:
                if request.GET.get('parse') and request.GET.get('parse') in ['True', 'true']:
                    response_data['sections'] = _parse_overview_html(existing_content)
                else:
                    response_data['overview_html'] = existing_content
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class CoursesUpdates(SecureAPIView):
    """
    **Use Case**

        CoursesUpdates returns an HTML representation of the overview for the
        specified course. CoursesUpdates has an optional parse parameter that
        when true breaks the response into a collection named postings. By
        default, parse is false.

    **Example Requests**

          GET /api/courses/{course_id}/updates

          GET /api/courses/{course_id}/updates?parse=true

    **Response Values**

        * content: The HTML representation of the course overview.
          Sections of the overview are indicated by an HTML section element.

        * postings: When parse=true, a collection of JSON objects representing
          parts of the course overview. Each element in postings contains a date
          and content key.
    """

    def get(self, request, course_id):
        response_data = OrderedDict()
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        content = get_course_info_section(request, existing_course, 'updates')
        if not content:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        if request.GET.get('parse') and request.GET.get('parse') in ['True', 'true']:
            response_data['postings'] = _parse_updates_html(content)
        else:
            response_data['content'] = content
        return Response(response_data)


class CoursesStaticTabsList(SecureAPIView):
    """
    **Use Case**

        CoursesStaticTabsList returns a collection of custom pages in the
        course. CoursesStaticTabsList has an optional detail parameter that when
        true includes the custom page content in the response.

    **Example Requests**

          GET /api/courses/{course_id}/static_tabs

          GET /api/courses/{course_id}/static_tabs?detail=true

    **Response Values**

        * tabs: The collection of custom pages in the course. Each object in the
          collection conains the following keys:

          * id: The ID of the custom page.

          * name: The Display Name of the custom page.

          * detail: When detail=true, the content of the custom page as HTML.
    """

    def get(self, request, course_id):
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data = OrderedDict()
        tabs = []
        for tab in existing_course.tabs:
            if tab.type == 'static_tab':
                tab_data = OrderedDict()
                tab_data['id'] = tab.url_slug
                tab_data['name'] = tab.name
                if request.GET.get('detail') and request.GET.get('detail') in ['True', 'true']:
                    tab_data['content'] = get_static_tab_contents(
                        request,
                        existing_course,
                        tab,
                        wrap_xmodule_display=False
                    )
                tabs.append(tab_data)
        response_data['tabs'] = tabs
        return Response(response_data)


class CoursesStaticTabsDetail(SecureAPIView):
    """
    **Use Case**

        CoursesStaticTabsDetail returns a collection of custom pages in the
        course, including the page content.

    **Example Requests**

          GET /api/courses/{course_id}/static_tabs/{tab_id}

    **Response Values**

        * tabs: The collection of custom pages in the course. Each object in the
          collection conains the following keys:

          * id: The ID of the custom page.

          * name: The Display Name of the custom page.

          * detail: The content of the custom page as HTML.
    """

    def get(self, request, course_id, tab_id):
        try:
            existing_course = get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data = OrderedDict()
        for tab in existing_course.tabs:
            if tab.type == 'static_tab' and tab.url_slug == tab_id:
                response_data['id'] = tab.url_slug
                response_data['name'] = tab.name
                response_data['content'] = get_static_tab_contents(
                    request,
                    existing_course,
                    tab,
                    wrap_xmodule_display=False
                )
        if not response_data:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        return Response(response_data, status=status.HTTP_200_OK)


class CoursesUsersList(SecureAPIView):
    """
    **Use Case**

        CoursesUsersList returns a collection of users enrolled or pre-enrolled
        in the course.

        You also use CoursesUsersList to enroll a new user in the course.

    **Example Requests**

          GET /api/courses/{course_id}/users

          POST /api/courses/{course_id}/users

    **GET Response Values**

        * enrollments: The collection of users in the course. Each object in the
          collection conains the following keys:

          * id: The ID of the user.

          * email: The email address of the user.

          * username: The username of the user.

    **Post Values**

        To create a new user through POST /api/courses/{course_id}/users, you
        must include either a user_id or email key in the JSON object.
    """

    def post(self, request, course_id):
        response_data = OrderedDict()
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        if 'user_id' in request.DATA:
            user_id = request.DATA['user_id']
            try:
                existing_user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
            CourseEnrollment.enroll(existing_user, course_id)
            return Response({}, status=status.HTTP_201_CREATED)
        elif 'email' in request.DATA:
            try:
                email = request.DATA['email']
                existing_user = User.objects.get(email=email)
            except ObjectDoesNotExist:
                if request.DATA.get('allow_pending'):
                    # If the email doesn't exist we assume the student does not exist
                    # and the instructor is pre-enrolling them
                    # Store the pre-enrollment data in the CourseEnrollmentAllowed table
                    # NOTE: This logic really should live in CourseEnrollment.....
                    cea, _ = CourseEnrollmentAllowed.objects.get_or_create(course_id=course_id, email=email)
                    cea.auto_enroll = True
                    cea.save()
                    return Response({}, status.HTTP_201_CREATED)
                else:
                    return Response({}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, course_id):
        response_data = OrderedDict()
        base_uri = generate_base_uri(request)
        response_data['uri'] = base_uri
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        # Get a list of all enrolled students
        users = CourseEnrollment.users_enrolled_in(course_id)
        response_data['enrollments'] = []
        for user in users:
            user_data = OrderedDict()
            user_data['id'] = user.id
            user_data['email'] = user.email
            user_data['username'] = user.username
            # @TODO: Should we create a URI resourse that points to user?!? But that's in a different URL subpath
            response_data['enrollments'].append(user_data)

        # Then list all enrollments which are pending. These are enrollments for students that have not yet
        # created an account
        pending_enrollments = CourseEnrollmentAllowed.objects.filter(course_id=course_id)
        if pending_enrollments:
            response_data['pending_enrollments'] = []
            for cea in pending_enrollments:
                response_data['pending_enrollments'].append(cea.email)
        return Response(response_data)


class CoursesUsersDetail(SecureAPIView):
    """
    **Use Case**

        CoursesUsersDetail returns a details about a specified user of a course.

        You also use CoursesUsersDetail to unenroll a user from the course.

    **Example Requests**

          GET /api/courses/{course_id}/users/{user_id}

          DELETE /api/courses/{course_id}/users/{user_id}

    **GET Response Values**

        * course_id: The ID of the course the user is enrolled in.

        * position: The last known position in the course. (??? in outline?)

        * user_id: The ID of the user.

        * uri: The URI to use to get details of the user.
    """
    def get(self, request, course_id, user_id):
        """
        GET /api/courses/{course_id}/users/{user_id}
        """
        base_uri = generate_base_uri(request)
        response_data = {
            'course_id': course_id,
            'user_id': user_id,
            'uri': base_uri,
        }
        try:
            course_descriptor = get_course(course_id)
        except ValueError:
            course_descriptor = None
        if not course_descriptor:
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except ObjectDoesNotExist:
            user = None
        if user and CourseEnrollment.is_enrolled(user, course_id):
            field_data_cache = FieldDataCache([course_descriptor], course_id, user)
            course_content = module_render.get_module(
                user,
                request,
                course_descriptor.location,
                field_data_cache,
                course_id)
            response_data['position'] = course_content.position
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def delete(self, request, course_id, user_id):
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except ObjectDoesNotExist:
            user = None
        if user:
            CourseEnrollment.unenroll(user, course_id)
        response_data = {}
        base_uri = generate_base_uri(request)
        response_data['uri'] = base_uri
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


class CourseContentGroupsList(SecureAPIView):
    """
    ### The CourseContentGroupsList view allows clients to retrieve a list of Content-Group relationships
    - URI: ```/api/courses/{course_id}/content/{content_id}/groups```
    - GET: Returns a JSON representation (array) of the set of Content-Group relationships
        * type: Set filtering parameter
    - POST: Creates a new CourseContentGroupRelationship entity using the provided Content and Group
        * group_id: __required__, The identifier for the Group being related to the Content
    - POST Example:

            {
                "group_id" : 12345
            }
    ### Use Cases/Notes:
    * Example: Link a specific piece of course content to a group, such as a student workgroup
    * Note: The specified Group must have a corresponding GroupProfile record for this operation to succeed
    * Providing a 'type' parameter will attempt to filter the related Group set by the specified value
    """

    def post(self, request, course_id, content_id):
        """
        POST /api/courses/{course_id}/content/{content_id}/groups
        """
        try:
            course_descriptor = get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        store = modulestore()
        try:
            existing_content = store.get_instance(course_id, Location(content_id))
        except InvalidLocationError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        group_id = request.DATA.get('group_id')
        if group_id is None:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            existing_profile = GroupProfile.objects.get(group_id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data = {}
        base_uri = generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, existing_profile.group_id)
        response_data['course_id'] = course_descriptor.id
        response_data['content_id'] = existing_content.id
        response_data['group_id'] = str(existing_profile.group_id)
        try:
            existing_relationship = CourseContentGroupRelationship.objects.get(
                course_id=course_id,
                content_id=content_id,
                group_profile=existing_profile
            )
            response_data['message'] = "Relationship already exists."
            return Response(response_data, status=status.HTTP_409_CONFLICT)
        except ObjectDoesNotExist:
            CourseContentGroupRelationship.objects.create(
                course_id=course_id,
                content_id=content_id,
                group_profile=existing_profile
            )
            return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request, course_id, content_id):
        """
        GET /api/courses/{course_id}/content/{content_id}/groups?type=workgroup
        """
        response_data = []
        group_type = request.QUERY_PARAMS.get('type')
        try:
            course_descriptor = get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            store = modulestore()
            existing_content = store.get_instance(course_id, Location(content_id))
        except InvalidLocationError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        relationships = CourseContentGroupRelationship.objects.filter(
            course_id=course_id,
            content_id=content_id,
        ).select_related("groupprofile")
        if group_type:
            relationships = relationships.filter(group_profile__group_type=group_type)
        response_data = [
            {'course_id': course_id, 'content_id': content_id, 'group_id': relationship.group_profile.group_id}
            for relationship in relationships
        ]
        return Response(response_data, status=status.HTTP_200_OK)


class CourseContentGroupsDetail(SecureAPIView):
    """
    ### The CourseContentGroupsDetail view allows clients to interact with a specific Content-Group relationship
    - URI: ```/api/courses/{course_id}/content/{content_id}/groups/{group_id}```
    - GET: Returns a JSON representation of the specified Content-Group relationship
    ### Use Cases/Notes:
    * Use the GET operation to verify the existence of a particular Content-Group relationship
    * If the User is enrolled in the course, we provide their last-known position to the client
    """
    def get(self, request, course_id, content_id, group_id):
        """
        GET /api/courses/{course_id}/content/{content_id}/groups/{group_id}
        """
        try:
            course_descriptor = get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            store = modulestore()
            existing_content = store.get_instance(course_id, Location(content_id))
        except InvalidLocationError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        try:
            relationship = CourseContentGroupRelationship.objects.get(
                course_id=course_id,
                content_id=content_id,
                group_profile__group_id=group_id
            )
        except ObjectDoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        response_data = {
            'course_id': course_id,
            'content_id': content_id,
            'group_id': group_id,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class CourseContentUsersList(SecureAPIView):
    """
    ### The CourseContentUsersList view allows clients to users enrolled and
    users not enrolled for course within all groups of course
    - URI: ```/api/courses/{course_id}/content/{content_id}/users
        * enrolled: boolean, filters user set by enrollment status
        * group_id: numeric, filters user set by membership in a specific group
        * type: string, filters user set by membership in groups matching the specified type
    - GET: Returns a JSON representation of users enrolled or not enrolled
    ### Use Cases/Notes:
    * Filtering related Users by enrollement status should be self-explanatory
    * An example of specific group filtering is to get the set of users who are members of a particular workgroup related to the content
    * An example of group type filtering is to get all users who are members of an organization group related to the content
    """

    def get(self, request, course_id, content_id):
        """
        GET /api/courses/{course_id}/content/{content_id}/users
        """
        enrolled = self.request.QUERY_PARAMS.get('enrolled', 'True')
        group_type = self.request.QUERY_PARAMS.get('type', None)
        group_id = self.request.QUERY_PARAMS.get('group_id', None)
        relationships = CourseContentGroupRelationship.objects.filter(
            course_id=course_id, content_id=content_id).select_related("groupprofile")

        if group_id:
            relationships = relationships.filter(group_profile__group__id=group_id)

        if group_type:
            relationships = relationships.filter(group_profile__group_type=group_type)

        lookup_group_ids = relationships.values_list('group_profile', flat=True)
        users = User.objects.filter(groups__id__in=lookup_group_ids)
        enrolled_users = CourseEnrollment.users_enrolled_in(course_id).filter(groups__id__in=lookup_group_ids)
        if enrolled in ['True', 'true']:
            queryset = enrolled_users
        else:
            queryset = list(itertools.ifilterfalse(lambda x: x in enrolled_users, users))

        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)  # pylint: disable=E1101


class CourseModuleCompletionList(SecureListAPIView):
    """
    ### The CourseModuleCompletionList allows clients to view user's course module completion entities
    to monitor a user's progression throughout the duration of a course,
    - URI: ```/api/courses/{course_id}/completions```
    - GET: Returns a JSON representation of the course, content and user and timestamps
    - GET Example:
        {
            "count":"1",
            "num_pages": "1",
            "previous": null
            "next": null
            "results": [
                {
                    "id": 2,
                    "user_id": "3",
                    "course_id": "32fgdf",
                    "content_id": "324dfgd",
                    "created": "2014-06-10T13:14:49.878Z",
                    "modified": "2014-06-10T13:14:49.914Z"
                }
            ]
        }

    Filters can also be applied
    ```/api/courses/{course_id}/completions/?user_id={user_id}```
    ```/api/courses/{course_id}/completions/?content_id={content_id}```
    ```/api/courses/{course_id}/completions/?user_id={user_id}&content_id={content_id}```
    - POST: Creates a Course-Module completion entity
    - POST Example:
        {
            "content_id":"i4x://the/content/location",
            "user_id":4
        }
    ### Use Cases/Notes:
    * Use GET operation to retrieve list of course completions by user
    * Use GET operation to verify user has completed specific course module
    """
    serializer_class = CourseModuleCompletionSerializer

    def get_queryset(self):
        """
        GET /api/courses/{course_id}/completions/
        """
        user_ids = self.request.QUERY_PARAMS.get('user_id', None)
        content_id = self.request.QUERY_PARAMS.get('content_id', None)
        course_id = self.kwargs['course_id']
        queryset = CourseModuleCompletion.objects.filter(course_id=course_id)
        upper_bound = getattr(settings, 'API_LOOKUP_UPPER_BOUND', 100)
        if user_ids:
            user_ids = map(int, user_ids.split(','))[:upper_bound]
            queryset = queryset.filter(user__in=user_ids)

        if content_id:
            queryset = queryset.filter(content_id=content_id)

        return queryset

    def post(self, request, course_id):
        """
        POST /api/courses/{course_id}/completions/
        """
        content_id = request.DATA.get('content_id', None)
        user_id = request.DATA.get('user_id', None)
        if not content_id:
            return Response({'message': _('content_id is missing')}, status.HTTP_400_BAD_REQUEST)
        if not user_id:
            return Response({'message': _('user_id is missing')}, status.HTTP_400_BAD_REQUEST)

        completion, created = CourseModuleCompletion.objects.get_or_create(user_id=user_id,
                                                                           course_id=course_id,
                                                                           content_id=content_id)
        serializer = CourseModuleCompletionSerializer(completion)
        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # pylint: disable=E1101
        else:
            return Response({'message': _('Resource already exists')}, status=status.HTTP_409_CONFLICT)


class CoursesGradesList(SecureListAPIView):
    """
    ### The CoursesGradesList view allows clients to retrieve a list of grades for the specified Course
    - URI: ```/api/courses/{course_id}/grades/```
    - GET: Returns a JSON representation (array) of the set of grade objects
    ### Use Cases/Notes:
    * Example: Display a graph of all of the grades awarded for a given course
    """

    def get(self, request, course_id):
        """
        GET /api/courses/{course_id}/grades?user_ids=1,2&content_ids=i4x://1/2/3,i4x://a/b/c
        """
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        queryset = StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            max_grade__isnull=False,
            max_grade__gt=0
        )

        upper_bound = getattr(settings, 'API_LOOKUP_UPPER_BOUND', 100)
        user_ids = self.request.QUERY_PARAMS.get('user_id', None)
        if user_ids:
            user_ids = map(int, user_ids.split(','))[:upper_bound]
            queryset = queryset.filter(student__in=user_ids)

        content_id = self.request.QUERY_PARAMS.get('content_id', None)
        if content_id:
            queryset = queryset.filter(module_state_key=content_id)

        queryset_grade_avg = queryset.aggregate(Avg('grade'))
        queryset_grade_sum = queryset.aggregate(Sum('grade'))
        queryset_maxgrade_sum = queryset.aggregate(Sum('max_grade'))

        course_queryset = StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            max_grade__isnull=False,
            max_grade__gt=0
        )
        course_queryset_grade_avg = course_queryset.aggregate(Avg('grade'))
        course_queryset_grade_sum = course_queryset.aggregate(Sum('grade'))
        course_queryset_maxgrade_sum = course_queryset.aggregate(Sum('max_grade'))

        response_data = {}
        base_uri = generate_base_uri(request)
        response_data['uri'] = base_uri
        response_data['average_grade'] = queryset_grade_avg['grade__avg']
        response_data['points_scored'] = queryset_grade_sum['grade__sum']
        response_data['points_possible'] = queryset_maxgrade_sum['max_grade__sum']
        response_data['course_average_grade'] = course_queryset_grade_avg['grade__avg']
        response_data['course_points_scored'] = course_queryset_grade_sum['grade__sum']
        response_data['course_points_possible'] = course_queryset_maxgrade_sum['max_grade__sum']

        response_data['grades'] = []
        for row in queryset:
            serializer = GradeSerializer(row)
            response_data['grades'].append(serializer.data)
        return Response(response_data, status=status.HTTP_200_OK)


class CoursesProjectList(SecureListAPIView):
    """
    ### The CoursesProjectList view allows clients to retrieve paginated list of projects by course
    - URI: ```/api/courses/{course_id}/projects/```
    - GET: Provides paginated list of projects for a course
    """

    serializer_class = ProjectSerializer

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            raise Http404

        return Project.objects.filter(course_id=course_id)


class CourseMetrics(SecureAPIView):
    """
    ### The CourseMetrics view allows clients to retrieve a list of Metrics for the specified Course
    - URI: ```/api/courses/{course_id}/metrics/```
    - GET: Returns a JSON representation (array) of the set of course metrics
    ### Use Cases/Notes:
    * Example: Display number of users enrolled in a given course
    """

    def get(self, request, course_id):  # pylint: disable=W0613
        """
        GET /api/courses/{course_id}/metrics/
        """
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if not existing_course:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        users_enrolled = CourseEnrollment.num_enrolled_in(course_id)
        data = {
            'users_enrolled': users_enrolled
        }
        return Response(data, status=status.HTTP_200_OK)


class CoursesLeadersList(SecureListAPIView):
    """
    ### The CoursesLeadersList view allows clients to retrieve ordered list of users who are leading
    in terms of points_scored for the specified Course
    - URI: ```/api/courses/{course_id}/metrics/proficiency/leaders/```
    - GET: Returns a JSON representation (array) of the users with points scored
    Filters can also be applied
    ```/api/courses/{course_id}/metrics/proficiency/leaders/?content_id={content_id}```
    To get top 3 users use count parameter
    ```/api/courses/{course_id}/metrics/proficiency/leaders/?count=3```
    ### Use Cases/Notes:
    * Example: Display leaderboard of a given course
    * Example: Display top 3 users of a given course
    """

    serializer_class = CourseLeadersSerializer

    def get_queryset(self):
        """
        GET /api/courses/{course_id}/metrics/proficiency/leaders/
        """
        course_id = self.kwargs['course_id']
        content_id = self.request.QUERY_PARAMS.get('content_id', None)
        count = self.request.QUERY_PARAMS.get('count', getattr(settings, 'API_LOOKUP_UPPER_BOUND', 100))
        try:
            get_course(course_id)
        except ValueError:
            raise Http404
        queryset = StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            max_grade__isnull=False,
            max_grade__gt=0
        )

        if content_id:
            queryset = queryset.filter(module_state_key=content_id)

        queryset = queryset.values('student__id', 'student__username', 'student__profile__title',
                                   'student__profile__avatar_url').annotate(points_scored=Sum('grade')).order_by('-points_scored')[:count]
        return queryset


class CoursesCompletionsLeadersList(SecureAPIView):
    """
    ### The CoursesCompletionsLeadersList view allows clients to retrieve top 3 users who are leading
    in terms of course module completions and course average for the specified Course, if user_id parameter is given
    position of user is returned
    - URI: ```/api/courses/{course_id}/metrics/completions/leaders/```
    - GET: Returns a JSON representation (array) of the users with points scored
    Filters can also be applied
    ```/api/courses/{course_id}/metrics/completions/leaders/?content_id={content_id}```
    To get more than 3 users use count parameter
    ```/api/courses/{course_id}/metrics/completions/leaders/?count=6```
    ### Use Cases/Notes:
    * Example: Display leaders in terms of completions in a given course
    * Example: Display top 3 users leading in terms of completions in a given course
    """

    def get(self, request, course_id):  # pylint: disable=W0613
        """
        GET /api/courses/{course_id}/metrics/completions/leaders/
        """
        user_id = self.request.QUERY_PARAMS.get('user_id', None)
        count = self.request.QUERY_PARAMS.get('count', 3)
        data = {}
        course_avg = 0
        try:
            get_course(course_id)
        except ValueError:
            raise Http404
        queryset = CourseModuleCompletion.objects.filter(course_id=course_id)

        if user_id:
            user_completions = queryset.filter(user__id=user_id).count()
            completions_above_user = queryset.filter(user__is_active=True).values('user__id')\
                .annotate(completions=Count('content_id')).filter(completions__gt=user_completions).count()
            data['position'] = completions_above_user + 1
            data['completions'] = user_completions

        total_completions = queryset.filter(user__is_active=True).count()
        users = CourseModuleCompletion.objects.filter(user__is_active=True)\
            .aggregate(total=Count('user__id', distinct=True))

        if users and users['total'] > 0:
            course_avg = round(total_completions / float(users['total']), 1)
        data['course_avg'] = course_avg

        queryset = queryset.filter(user__is_active=True).values('user__id', 'user__username', 'user__profile__title',
                                                                'user__profile__avatar_url')\
            .annotate(completions=Count('content_id')).order_by('-completions')[:count]
        serializer = CourseCompletionsLeadersSerializer(queryset, many=True)
        data['leaders'] = serializer.data  # pylint: disable=E1101
        return Response(data, status=status.HTTP_200_OK)
