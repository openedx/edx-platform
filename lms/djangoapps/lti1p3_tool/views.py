import json
import logging

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lti_provider.views import render_courseware
from util.views import add_p3p_header
from edxmako.shortcuts import render_to_string
from mako.template import Template
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from pylti1p3.contrib.django import DjangoOIDCLogin
from pylti1p3.exception import OIDCException, LtiException
from pylti1p3.lineitem import LineItem
from .tool_conf import ToolConfDb
from .message_launch import ExtendedDjangoMessageLaunch
from .models import GradedAssignment
from .users import Lti1p3UserService
from .utils import get_lineitem_tag


log = logging.getLogger("edx.lti1p3_tool")


@csrf_exempt
@add_p3p_header
def login(request):
    if not settings.FEATURES['ENABLE_LTI_PROVIDER']:
        return HttpResponseForbidden()

    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    if not target_link_uri:
        return render_lti_error('Missing "target_link_uri" param', 400)

    tool_conf = ToolConfDb()
    oidc_login = DjangoOIDCLogin(request, tool_conf)
    try:
        return oidc_login.redirect(target_link_uri)
    except OIDCException as e:
        return render_lti_error(str(e), 403)


@csrf_exempt
@add_p3p_header
@require_POST
def launch(request, usage_id=None):
    if not usage_id:
        usage_id = request.GET.get('block_id')

    block, err_tpl = get_block_by_id(usage_id)
    if not block:
        return err_tpl

    tool_conf = ToolConfDb()
    try:
        message_launch = ExtendedDjangoMessageLaunch(request, tool_conf)
        message_launch_data = message_launch.get_launch_data()
        lti_tool = message_launch.get_lti_tool()
    except LtiException as e:
        return render_lti_error(str(e), 403)

    log.info("LTI 1.3 JWT body: %s for block: %s", json.dumps(message_launch_data), usage_id)

    lti_jwt_sub = message_launch_data.get('sub')

    us = Lti1p3UserService()
    us.authenticate_lti_user(request, lti_jwt_sub, lti_tool)

    course_key = block.location.course_key
    usage_key = block.location

    if message_launch.has_ags():
        update_graded_assignment(lti_tool, message_launch, block, course_key, usage_key, request.user)
    else:
        log.warning("LTI1.3 platform doesn't support assignments and grades service: %s", lti_tool.issuer)

    return render_courseware(request, usage_key)


def get_block_by_id(block_id):
    try:
        if block_id:
            block_id = UsageKey.from_string(block_id)
    except InvalidKeyError:
        block_id = None

    if not block_id:
        return False, render_lti_error('Invalid URL', 400)
    else:
        try:
            block = modulestore().get_item(block_id)
            return block, False
        except ItemNotFoundError:
            return False, render_lti_error('Block not found', 404)


def render_lti_error(message, http_code=None):
    template = Template(render_to_string('static_templates/lti1p3_error.html', {
        'message': message,
        'http_code': http_code
    }))
    if http_code == 400:
        return HttpResponseBadRequest(template.render())
    elif http_code == 403:
        return HttpResponseForbidden(template.render())
    elif http_code == 404:
        return HttpResponseNotFound(template.render())
    return HttpResponse(template.render())


def update_graded_assignment(lti_tool, message_launch, block, course_key, usage_key, user):
    ags = message_launch.get_ags()
    message_launch_data = message_launch.get_launch_data()

    lti_jwt_sub = message_launch_data.get('sub')
    endpoint = message_launch_data.get('https://purl.imsglobal.org/spec/lti-ags/claim/endpoint', {})
    lineitem = endpoint.get('lineitem')

    # if lineitem was passed in JWT body
    if lineitem:
        # try to find existing GradedAssignment or create the new one
        try:
            GradedAssignment.objects.get(
                lti_lineitem=lineitem,
                lti_jwt_sub=lti_jwt_sub
            )
        except GradedAssignment.DoesNotExist:
            gr = GradedAssignment(
                user=user,
                course_key=course_key,
                usage_key=usage_key,
                lti_tool=lti_tool,
                lti_jwt_endpoint=endpoint,
                lti_jwt_sub=lti_jwt_sub,
                lti_lineitem=lineitem,
                lti_lineitem_tag=None,
                created_by_tool=False
            )
            gr.save()

    # if lineitem wasn't passed in JWT body but item is graded
    # we may create lineitem forcibly
    elif lti_tool.force_create_lineitem and block.graded:
        lti_lineitem_tag = get_lineitem_tag(usage_key)
        # try to find existing GradedAssignment or create the new one
        try:
            GradedAssignment.objects.get(
                lti_jwt_sub=lti_jwt_sub,
                lti_lineitem_tag=lti_lineitem_tag
            )
        except GradedAssignment.DoesNotExist:
            course = modulestore().get_course(course_key, depth=0)
            course_grade = CourseGradeFactory().read(user, course)
            earned, possible = course_grade.score_for_module(usage_key)

            line_item = LineItem()
            line_item.set_tag(lti_lineitem_tag) \
                .set_score_maximum(possible) \
                .set_label(block.display_name)
            line_item = ags.find_or_create_lineitem(line_item)
            gr = GradedAssignment(
                user=user,
                course_key=course_key,
                usage_key=usage_key,
                lti_tool=lti_tool,
                lti_jwt_endpoint=endpoint,
                lti_jwt_sub=lti_jwt_sub,
                lti_lineitem=line_item.get_id(),
                lti_lineitem_tag=lti_lineitem_tag,
                created_by_tool=True
            )
            gr.save()
    else:
        log.info("LTI1.3 platform didn't pass lineitem [issuer=%s, course_key=%s, usage_key=%s, user_id=%d]",
                 lti_tool.issuer, str(course_key), str(usage_key), user.id)
