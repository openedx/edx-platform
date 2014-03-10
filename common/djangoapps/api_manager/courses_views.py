""" API implementation for course-oriented interactions. """

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_manager.permissions import ApiKeyHeaderPermission
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location, InvalidLocationError


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
