""" API implementation for Secure api calls. """

import socket
import struct

from courseware import module_render, courses
from courseware.model_data import FieldDataCache
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from xmodule.modulestore import InvalidLocationError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def address_exists_in_network(ip_address, net_n_bits):
    """
    return True if the ip address exists in the subnet address
    otherwise return False
    """
    ip_address = struct.unpack('<L', socket.inet_aton(ip_address))[0]
    net, bits = net_n_bits.split('/')
    net_address = struct.unpack('<L', socket.inet_aton(net))[0]
    net_mask = ((1L << int(bits)) - 1)
    return ip_address & net_mask == net_address & net_mask


def get_client_ip_address(request):
    """
    get the client IP Address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[-1].strip()
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    return ip_address


def str2bool(value):
    """
    convert string to bool
    """
    return value.lower() in ("true",)


def generate_base_uri(request, strip_qs=False):
    """
    Build absolute uri
    """
    if strip_qs:
        return request.build_absolute_uri(request.path)  # Don't need querystring that why giving location parameter
    else:
        return request.build_absolute_uri()


def is_int(value):
    """
    checks if a string value can be interpreted as integer
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def get_course(request, user, course_id, depth=0):
    """
    Utility method to obtain course components
    """
    course_descriptor = None
    course_key = None
    course_content = None
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            pass
    if course_key:
        try:
            course_descriptor = courses.get_course(course_key, depth)
        except ValueError:
            pass
    if course_descriptor:
        field_data_cache = FieldDataCache([course_descriptor], course_key, user)
        course_content = module_render.get_module(
            user,
            request,
            course_descriptor.location,
            field_data_cache,
            course_key)
    return course_descriptor, course_key, course_content


def get_course_child(request, user, course_key, content_id):
    """
    Return a course xmodule/xblock to the caller
    """
    content_descriptor = None
    content_key = None
    content = None
    try:
        content_key = UsageKey.from_string(content_id)
    except InvalidKeyError:
        try:
            content_key = Location.from_deprecated_string(content_id)
        except (InvalidLocationError, InvalidKeyError):
            pass
    if content_key:
        try:
            content_descriptor = modulestore().get_item(content_key)
        except ItemNotFoundError:
            pass
        if content_descriptor:
            field_data_cache = FieldDataCache([content_descriptor], course_key, user)
            content = module_render.get_module(
                user,
                request,
                content_key,
                field_data_cache,
                course_key)
    return content_descriptor, content_key, content


def get_course_total_score(course_summary):
    """
    Traverse course summary to calculate max possible score for a course
    """
    score = 0
    for chapter in course_summary:  # accumulate score of each chapter
        for section in chapter['sections']:
            if section['section_total']:
                score += section['section_total'][1]
    return score
