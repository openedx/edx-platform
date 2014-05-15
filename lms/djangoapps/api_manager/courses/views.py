""" API implementation for course-oriented interactions. """

from collections import OrderedDict
import logging
import itertools
from lxml import etree
from StringIO import StringIO

from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from api_manager.permissions import ApiKeyHeaderPermission
from api_manager.models import CourseGroupRelationship, CourseContentGroupRelationship, GroupProfile
from api_manager.users.serializers import UserSerializer
from courseware import module_render
from courseware.courses import get_course, get_course_about_section, get_course_info_section
from courseware.model_data import FieldDataCache
from courseware.views import get_static_tab_contents
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location, InvalidLocationError


log = logging.getLogger(__name__)


def _generate_base_uri(request):
    """
    Constructs the protocol:host:path component of the resource uri
    """
    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    resource_uri = '{}://{}{}'.format(
        protocol,
        request.get_host(),
        request.get_full_path()
    )
    return resource_uri


def _get_content_children(content, content_type=None):
    """
    Parses the provided content object looking for children
    Matches on child type (category) when specified
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
    Helper method to break up the course updates HTML into components
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


class CourseContentList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id, content_id=None):
        """
        GET retrieves the list of children for a given content object
        We don't know where in the content hierarchy we are -- could even be the top
        """
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


class CourseContentDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id, content_id):
        """
        GET retrieves an existing content object from the system
        """
        store = modulestore()
        response_data = {}
        content_type = request.QUERY_PARAMS.get('type', None)
        if course_id != content_id:
            element_name = 'children'
            try:
                content = store.get_instance(course_id, Location(content_id))
            except InvalidLocationError:
                content = None
        else:
            element_name = 'content'
            content = get_course(course_id)
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
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=status_code)


class CoursesList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request):
        """
        GET returns the list of available courses
        """
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


class CoursesDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id):
        """
        GET retrieves an existing course from the system and returns
        summary information about its content children to the specified depth
        """
        depth = request.QUERY_PARAMS.get('depth', 0)
        depth_int = int(depth)
        # get_course_by_id raises an Http404 if the requested course is invalid
        # Rather than catching it, we just let it bubble up
        try:
            course_descriptor = get_course(course_id, depth=depth_int)
        except ValueError:
            course_descriptor = None
        if course_descriptor:
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
            status_code = status.HTTP_200_OK
            response_data['uri'] = _generate_base_uri(request)
            return Response(response_data, status=status_code)
        else:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class CoursesGroupsList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, course_id):
        """
        POST creates a new course-group relationship in the system
        """
        response_data = {}
        group_id = request.DATA['group_id']
        base_uri = _generate_base_uri(request)
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
        GET retrieves the list of groups related to the specified course
        """
        try:
            get_course(course_id)
        except ValueError:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        group_type = request.QUERY_PARAMS.get('type', None)
        course_groups = CourseGroupRelationship.objects.filter(course_id=course_id)

        if group_type:
            course_groups = course_groups.filter(group__groupprofile__group_type=group_type)
        response_data = {'groups': []}
        for course_group in course_groups:
            group_profile = GroupProfile.objects.get(group_id=course_group.group_id)
            group_data = {'id': course_group.group_id, 'name': group_profile.name}
            response_data['groups'].append(group_data)
        response_status = status.HTTP_200_OK
        return Response(response_data, status=response_status)

class CoursesGroupsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id, group_id):
        """
        GET retrieves an existing course-group relationship from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = base_uri
        response_data['course_id'] = course_id
        response_data['group_id'] = group_id
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
            if existing_relationship:
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_404_NOT_FOUND
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def delete(self, request, course_id, group_id):
        """
        DELETE removes/inactivates/etc. an existing course-group relationship
        """
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group).delete()
        except ObjectDoesNotExist:
            pass
        response_data = {}
        response_data['uri'] = _generate_base_uri(request)
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


class CoursesOverview(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id):
        """
        GET retrieves the course overview content, which - in MongoDB - is stored with the following
        naming convention {"_id.org":"i4x", "_id.course":<course_num>, "_id.category":"about", "_id.name":"overview"}
        """
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


class CoursesUpdates(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id):
        """
        GET retrieves the course overview content, which - in MongoDB - is stored with the following
        naming convention {"_id.org":"i4x", "_id.course":<course_num>, "_id.category":"course_info", "_id.name":"updates"}
        """
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


class CoursesStaticTabsList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id):
        """
        GET returns an array of Static Tabs inside of a course
        """
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


class CoursesStaticTabsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id, tab_id):
        """
        GET returns the specified static tab for the specified course
        """
        try:
            existing_course = get_course(course_id)
        except ValueError:
            existing_course = None
        if existing_course:
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
        else:
            return Response({}, status=status.HTTP_404_NOT_FOUND)


class CoursesUsersList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, course_id):
        """
        POST enrolls a student in the course. Note, this can be a user_id or
        just an email, in case the user does not exist in the system
        """
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
                existing_user = None
            if existing_user:
                CourseEnrollment.enroll(existing_user, course_id)
                return Response({}, status=status.HTTP_201_CREATED)
            else:
                return Response({}, status=status.HTTP_404_NOT_FOUND)
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
        """
        GET returns a list of users enrolled in the course_id
        """
        response_data = OrderedDict()
        base_uri = _generate_base_uri(request)
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


class CoursesUsersDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id, user_id):
        """
        GET identifies an ACTIVE course enrollment for the specified user
        """
        base_uri = _generate_base_uri(request)
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
        """
        DELETE unenrolls the specified user from the specified course
        """
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
        base_uri = _generate_base_uri(request)
        response_data['uri'] = base_uri
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


class CourseContentGroupsList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, course_id, content_id):
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
        try:
            existing_relationship = CourseContentGroupRelationship.objects.get(
                course_id=course_id,
                content_id=content_id,
                group_profile=existing_profile
            )
        except ObjectDoesNotExist:
            existing_relationship = None
        response_data = {}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, existing_profile.group_id)
        if existing_relationship:
            response_data['message'] = "Relationship already exists."
            return Response(response_data, status=status.HTTP_409_CONFLICT)
        CourseContentGroupRelationship.objects.create(
            course_id=course_id,
            content_id=content_id,
            group_profile=existing_profile
        )
        rels = CourseContentGroupRelationship.objects.all()
        for rel in rels:
            print rel.__dict__
        response_data['course_id'] = course_descriptor.id
        response_data['content_id'] = existing_content.id
        response_data['group_id'] = str(existing_profile.group_id)
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request, course_id, content_id):
        """
        GET retrieves the list of groups for a given content object.
        The 'type' query parameter is available for filtering by group_type
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


class CourseContentGroupsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, course_id, content_id, group_id):
        """
        GET retrieves an existing content-group relationship from the system
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


class CourseContentUsersList(generics.ListAPIView):
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
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer

    def get_queryset(self):
        """
        GET /api/courses/{course_id}/content/{content_id}/users
        """
        course_id = self.kwargs['course_id']
        content_id = self.kwargs['content_id']
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
        return queryset
