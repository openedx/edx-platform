""" API implementation for course-oriented interactions. """

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_manager.permissions import ApiKeyHeaderPermission
from api_manager.models import CourseGroupRelationship
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location, InvalidLocationError


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
        request.path
    )
    return resource_uri


def _get_module_submodules(module, submodule_type=None):
    """
    Parses the provided module looking for child modules
    Matches on submodule type (category) when specified
    """
    submodules = []
    if hasattr(module, 'children'):
        child_modules = module.get_children()
        for child_module in child_modules:
            if submodule_type:
                if getattr(child_module, 'category') == submodule_type:
                    submodules.append(child_module)
            else:
                submodules.append(child_module)
    return submodules


def _serialize_module(request, course_id, module):
    """
    Loads the specified module data into the response dict
    This should probably evolve to use DRF serializers
    """
    data = {}

    if getattr(module, 'id') == course_id:
        module_id = module.id
    else:
        module_id = module.location.url()
    data['id'] = module_id

    if hasattr(module, 'display_name'):
        data['name'] = module.display_name

    data['category'] = module.location.category

    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    module_uri = '{}://{}/api/courses/{}'.format(
        protocol,
        request.get_host(),
        course_id.encode('utf-8')
    )

    # Some things we do only if the module is a course
    if (course_id == module_id):
        data['number'] = module.location.course
        data['org'] = module.location.org

    # Other things we do only if the module is not a course
    else:
        module_uri = '{}/modules/{}'.format(module_uri, module_id)
    data['uri'] = module_uri

    return data


def _serialize_module_submodules(request, course_id, submodules):
    """
    Loads the specified module submodule data into the response dict
    This should probably evolve to use DRF serializers
    """
    data = []
    if submodules:
        for submodule in submodules:
            submodule_data = _serialize_module(
                request,
                course_id,
                submodule
            )
            data.append(submodule_data)
    return data


@api_view(['GET'])
@permission_classes((ApiKeyHeaderPermission,))
def modules_list(request, course_id, module_id=None):
    """
    GET retrieves the list of submodules for a given module
    We don't know where in the module hierarchy we are -- could even be the top
    """
    if module_id is None:
        module_id = course_id
    response_data = []
    submodule_type = request.QUERY_PARAMS.get('type', None)
    store = modulestore()
    if course_id != module_id:
        try:
            module = store.get_instance(course_id, Location(module_id))
        except InvalidLocationError:
            module = None
    else:
        module = store.get_course(course_id)
    if module:
        submodules = _get_module_submodules(module, submodule_type)
        response_data = _serialize_module_submodules(
            request,
            course_id,
            submodules
        )
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_404_NOT_FOUND
    return Response(response_data, status=status_code)


@api_view(['GET'])
@permission_classes((ApiKeyHeaderPermission,))
def modules_detail(request, course_id, module_id):
    """
    GET retrieves an existing module from the system
    """
    store = modulestore()
    response_data = {}
    submodule_type = request.QUERY_PARAMS.get('type', None)
    if course_id != module_id:
        try:
            module = store.get_instance(course_id, Location(module_id))
        except InvalidLocationError:
            module = None
    else:
        module = store.get_course(course_id)
    if module:
        response_data = _serialize_module(
            request,
            course_id,
            module
        )
        submodules = _get_module_submodules(module, submodule_type)
        response_data['modules'] = _serialize_module_submodules(
            request,
            course_id,
            submodules
        )
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_404_NOT_FOUND
    return Response(response_data, status=status_code)


@api_view(['GET'])
@permission_classes((ApiKeyHeaderPermission,))
def courses_list(request):
    """
    GET returns the list of available courses
    """
    response_data = []
    store = modulestore()
    course_descriptors = store.get_courses()
    for course_descriptor in course_descriptors:
        course_data = _serialize_module(
            request,
            course_descriptor.id,
            course_descriptor
        )
        response_data.append(course_data)
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((ApiKeyHeaderPermission,))
def courses_detail(request, course_id):
    """
    GET retrieves an existing course from the system
    """
    response_data = {}
    store = modulestore()
    try:
        course_descriptor = store.get_course(course_id)
    except ValueError:
        course_descriptor = None
    if course_descriptor:
        response_data = _serialize_module(
            request,
            course_descriptor.id,
            course_descriptor
        )
        submodules = _get_module_submodules(course_descriptor, None)
        response_data['modules'] = _serialize_module_submodules(
            request,
            course_id,
            submodules
        )
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_404_NOT_FOUND
    return Response(response_data, status=status_code)


@api_view(['POST'])
@permission_classes((ApiKeyHeaderPermission,))
def courses_groups_list(request, course_id):
    """
    POST creates a new course-group relationship in the system
    """
    response_data = {}
    group_id = request.DATA['group_id']
    base_uri = _generate_base_uri(request)
    store = modulestore()
    try:
        existing_course = store.get_course(course_id)
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


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def courses_groups_detail(request, course_id, group_id):
    """
    GET retrieves an existing course-group relationship from the system
    DELETE removes/inactivates/etc. an existing course-group relationship
    """
    if request.method == 'GET':
        response_data = {}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = base_uri
        response_data['course_id'] = course_id
        response_data['group_id'] = group_id
        store = modulestore()
        try:
            existing_course = store.get_course(course_id)
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
    elif request.method == 'DELETE':
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group).delete()
        except ObjectDoesNotExist:
            pass
        return Response({}, status=status.HTTP_204_NO_CONTENT)
