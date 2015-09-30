""" Labster Course views. """
import logging

from django.http import Http404, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.reverse import reverse
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from util.json_request import JsonResponse, expect_json
from contentstore.views.course import _create_or_rerun_course
from contentstore.utils import delete_course_and_groups
from labster.course.utils import set_staff, contains, get_simulation_id, get_parent_xblock, strip_object
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor


log = logging.getLogger(__name__)


class LicenseStoreError(Exception):
    """
    An error thrown when a LicenseStore input is invalid.
    """
    pass


class LicenseStore(object):
    """
    A small class that is used to prepare, store and easy access the licenses.

    Input format:
    [
        {
            "id": "a04m00000099jAJAAY",
                "simulations": [{"simulation": "a05m0000002N3YgAAK"}]
        },
        {
            "id": "Aqk38uVQnA",
            "simulations": [
                {"simulation": "6364d3f0f495b6ab9dcf8d3b5c6e0b01"},
                {"simulation": "d67d8ab4f4c10bf22aa353e27879133c"},
                {"simulation": "9bf31c7ff062936a96d3c8bd1f8f2ff3"},
            ]
        }
    ]
    """
    def __init__(self, licenses):
        self._initial = licenses
        self._licenses = {s['simulation']: l['id'] for l in licenses for s in l['simulations']}

    def get(self, simulation_id):
        """
        Returns a license id for the passed `simulation_id`(str).
        """
        return self._licenses.get(simulation_id)

    @staticmethod
    def factory(licenses):
        try:
            return LicenseStore(licenses)
        except Exception:
            raise LicenseStoreError


class XBlockInfo(object):
    def __init__(self, info=None):
        self.is_hidden = info.is_hidden if info else True
        self.children = list(info.children) if info else []

    def set_visibility(self, value):
        if self.is_hidden is not False:
            self.is_hidden = value


def get_xblock_info(xblock, cache, is_hidden=True, child=None):
    """
    Returns information (`is_hidden`(bool), `children`(list)) about the xblock.
    """
    info = XBlockInfo(cache.get(xblock))
    info.set_visibility(is_hidden)
    if child is not None:
        info.children.append(child)
    return info


def update_visibility_to_staff(store, user_id, cache, descriptors):
    """
    Updates all the xblocks that have changed `visible_to_staff_only` parameter.
    """
    for descriptor in descriptors:
        info = cache[descriptor]
        if descriptor.visible_to_staff_only != info.is_hidden:
            item = store.get_item(strip_object(descriptor.location))
            item.visible_to_staff_only = info.is_hidden
            item.save()
            store.update_item(item, user_id)
        update_visibility_to_staff(store, user_id, cache, info.children)


def update_lti_license(xblock, license):
    """
    Updates/adds custom parameter `license`.
    """
    license_string = 'license={}'.format(license)
    index = contains(xblock.custom_parameters, 'license')
    # If a custom param doesn't present, just add it.
    if index == -1:
        if license is not None:
            xblock.custom_parameters.append(license_string)
        else:
            return False
    # Otherwise, replace current license by the new one.
    else:
        if license is None:
            del xblock.custom_parameters[index]
        else:
            xblock.custom_parameters[index] = license_string
    return True


def setup_course(course_key, user_id, license_storage, staff=None):
    """
    Updates course staff and licenses.
    """
    if staff is not None:
        set_staff(course_key, staff)

    store = modulestore()
    with store.bulk_operations(course_key):
        cache = {}
        simulations = store.get_items(course_key, qualifiers={'category': 'lti'})
        for simulation in simulations:
            simulation_id = get_simulation_id(simulation.launch_url)
            if update_lti_license(simulation, license_storage.get(simulation_id)):
                simulation.save()
                simulation = store.update_item(simulation, user_id)

            if license_storage.get(simulation_id) is None:
                unit = get_parent_xblock(simulation, child_for='sequential')
                if unit is None:
                    log.debug('Cannot find ancestor for the xblock: %s', simulation)
                    continue
                cache[unit] = get_xblock_info(unit, cache, is_hidden=True)

                subsection = unit.get_parent()
                if subsection is None:
                    log.debug('Cannot find ancestor for the xblock: %s', unit)
                    continue
                cache[subsection] = get_xblock_info(subsection, cache, is_hidden=True, child=unit)

                chapter = subsection.get_parent()
                if chapter is None:
                    log.debug('Cannot find ancestor for the xblock: %s', subsection)
                    continue
                cache[chapter] = get_xblock_info(chapter, cache, is_hidden=True, child=subsection)
            else:
                subsection = get_parent_xblock(simulation, child_for='chapter')
                if subsection is None:
                    log.debug('Cannot find ancestor for the xblock: %s', simulation)
                    continue
                cache[subsection] = get_xblock_info(subsection, cache, is_hidden=False)

                chapter = subsection.get_parent()
                if chapter is None:
                    log.debug('Cannot find ancestor for the xblock: %s', subsection)
                    continue
                cache[chapter] = get_xblock_info(chapter, cache, is_hidden=False)

        chapters = filter(lambda x: getattr(x, 'category') == 'chapter', cache.keys())
        update_visibility_to_staff(store, user_id, cache, chapters)


# pylint: disable=unused-argument
@csrf_exempt
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@authentication_classes((OAuth2Authentication, SessionAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
@expect_json
def course_handler(request, course_key_string=None):
    """
    **Use Case**
        Get a list of course keys. Create, duplicate or delete a course.

    **Example requests**:
        GET /labster/api/course/?org={course_org}&number={course_number}
            /labster/api/course/?org=labster&number=labx

        POST /labster/api/course/
        {
            "org": "labster",
            "number": "LABX1",
            "display_name": "Duplicated Course 1",
            "run": "2015_T2",
            "source_course_key": "course-v1:labster+LABX+2015_T1",
            "staff": ["honor@example.com", "staff@example.com"],
            "licenses": [
                {
                    "id":"a04m00000099jAJAAY",
                    "simulations": [{"simulation":"a05m0000002N3YgAAK"}]
                },
                {
                    "id":"Aqk38uVQnA",
                    "simulations":[
                        {"simulation":"6364d3f0f495b6ab9dcf8d3b5c6e0b01"},
                        {"simulation":"d67d8ab4f4c10bf22aa353e27879133c"},
                        {"simulation":"9bf31c7ff062936a96d3c8bd1f8f2ff3"}
                    ]
                }
            ]
        }

        PUT    /labster/api/course/{course_key}/
               /labster/api/course/course-v1:labster+LABX+2015_T2/
        {
            "staff": ["honor@example.com", "staff@example.com"],
            "licenses": [
                {
                    "id":"a04m00000099jAJAAY",
                    "simulations": [{"simulation":"a05m0000002N3YgAAK"}]
                },
                {
                    "id":"Aqk38uVQnA",
                    "simulations":[
                        {"simulation":"6364d3f0f495b6ab9dcf8d3b5c6e0b01"},
                        {"simulation":"d67d8ab4f4c10bf22aa353e27879133c"},
                        {"simulation":"9bf31c7ff062936a96d3c8bd1f8f2ff3"}
                    ]
                }
            ]
        }

        DELETE /labster/api/course/{course_key}/
               /labster/api/course/course-v1:labster+LABX+2015_T2/

    **Request Parameters**
        * display_name: The public display name for the new course.

        * org: The name of the organization sponsoring the new course.
          Note: No spaces or special characters are allowed.

        * number: The unique number that identifies the new course within the organization.
          Note: No spaces or special characters are allowed.

        * run: The term in which the new course will run.
          Note: No spaces or special characters are allowed.

        * start: The start date for the course.

        * source_course_key(optional): The source course (The course which is duplicated).

        * licenses: The list of licenses.

        * staff: The list of staff emails to add to the course.
    """
    try:
        if request.method in ('GET', 'POST'):
            if request.method == 'POST':
                store = modulestore()
                with store.default_store('split'):
                    org = request.json.get('org')
                    number = request.json.get('number', request.json.get('course'))
                    run = request.json.get('run')
                    destination_course_key = store.make_course_key(org, number, run)

                response = _create_or_rerun_course(request)
                setup_course(
                    destination_course_key,
                    user_id=request.user.id,
                    license_storage=LicenseStore.factory(request.json.get('licenses')),
                    staff=request.json.get('staff')
                )
                return response

            elif request.method == 'GET':
                filter_by_org = request.GET.get('org')
                filter_by_number = request.GET.get('number')
                courses = modulestore().get_courses(org=filter_by_org)
                courses = filter(lambda c: isinstance(c, CourseDescriptor), courses)

                if filter_by_number:
                    courses = filter(lambda c: c.number.lower() == filter_by_number.lower(), courses)

                return Response([
                    {
                        "display_name": course.display_name,
                        "course_key": unicode(course.location.course_key)
                    } for course in courses
                ])

        elif request.method in ('PUT', 'DELETE'):
            course_key = CourseKey.from_string(course_key_string)
            if request.method == 'PUT':
                setup_course(
                    course_key,
                    user_id=request.user.id,
                    license_storage=LicenseStore.factory(request.json.get('licenses')),
                    staff=request.json.get('staff')
                )
                return Response({"course_key": unicode(course_key)})
            elif request.method == 'DELETE':
                delete_course_and_groups(course_key, request.user.id)
                return Response(status=status.HTTP_204_NO_CONTENT)

    except LicenseStoreError:
        raise HttpResponseBadRequest({
            'ErrMsg': 'Incorrect license format.'
        })
    except InvalidKeyError:
        raise Http404
