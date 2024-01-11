import json
import re
import bleach
import html
from bleach.css_sanitizer import CSSSanitizer
from common.djangoapps.edxmako.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import PermissionDenied
from cms.djangoapps.contentstore.views.certificates import _get_course_and_check_access
from common.djangoapps.util.json_request import JsonResponse
from opaque_keys.edx.keys import  CourseKey
from common.djangoapps.edxmako.shortcuts import render_to_response
from cms.djangoapps.contentstore.views.item import _save_xblock 
import openpyxl
from django.views.decorators.http import require_http_methods
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rest_framework import status
from django.http import JsonResponse
from cms.djangoapps.contentstore.views.item import _save_xblock, _get_xblock
from opaque_keys.edx.keys import  CourseKey
from xmodule.modulestore.django import modulestore

# component class, display text, should render on client side, title attribute on client side
COMPONENT_TYPES = [
    ("HtmlBlockWithMixins", "Text Components", True, 'Remove Text Component Styles'),
    ("ProblemBlockWithMixins", "Problem Components", False, 'Remove Problem Component Styles'),
    ("LabXBlockWithMixins", "Lab", False, ''),
    ("VideoBlockWithMixins", "Video", False, ''),
    ("LibraryContentBlockWithMixins", "Library", False, ''),
    ("AssignmentXBlockWithMixins", "Learning Project", False, ''),
    ("DiscussionXBlockWithMixins", "Discussion", False, ''),
    ("OpenAssessmentBlockWithMixins", "OpenAssessment", False, ''),
]

@require_http_methods(['GET', 'POST'])
@login_required
@ensure_csrf_cookie
def remove_inline_styles(request, course_id):
    course_key = CourseKey.from_string(course_id)
    
    try:
        course = _get_course_and_check_access(course_key, request.user)
    except PermissionDenied:
        return JsonResponse({"message": 'Permission Denied'}, status=403)

    context = {
        'context_course': course,
        'component_types': list(filter(lambda item: item[2], COMPONENT_TYPES))
    }

    if request.method == 'GET':
        return render_to_response('funix_remove_inline_style.html', context)

    # PUT
    component_types = json.loads(request.body).get('component_types')
    if len(component_types) == 0:
        component_types = ['HtmlBlockWithMixins']

    course_overview = CourseOverview.get_from_id(course_id)
    if not course_overview:
        return JsonResponse(data={
            "message": f"Not found course with course_code '{course_id}'",
        }, status=status.HTTP_400_BAD_REQUEST)

    course = course_overview._original_course
    sections = course.get_children()
    
    remove_errors = []
    remove_success = []
    publish_errors = []
    publish_success = []

    for section in sections:
        subsections = section.get_children()
        for sub in subsections:
            units = sub.get_children()
            for unit in units:
                components = unit.get_children()
                for component in components:
                    if type(component).__name__ in component_types:
                        usage_key = component.scope_ids.usage_id
                        try:
                            _save_xblock(
                                request.user,
                                _get_xblock(usage_key, request.user),
                                data=_remove_style(component.data),
                                children_strings=None,
                                metadata={},
                                nullout=None,
                                grader_type=None,
                                is_prereq=None,
                                prereq_usage_key=None,
                                prereq_min_score=None,
                                prereq_min_completion=None,
                                publish=None,
                                fields=None,
                            )
                            success_msg = f"{sub.display_name}, {unit.display_name}, {component.display_name}"
                            remove_success.append(success_msg)
                        except Exception as e:
                            print(str(e))
                            error_msg = f"{sub.display_name}, {unit.display_name}, {component.display_name}: {str(e)}"
                            print(error_msg, type(component).__name__, component.data)
                            remove_errors.append(error_msg)
    

    if json.loads(request.body).get('publish'):
        for section in sections:
            try:
                modulestore().publish(section.location, request.user.id)
                publish_success.append(section.display_name)
            except Exception as e:
                msg = f"Failed to publish section {section.display_name}: {str(e)}"
                print(msg)
                publish_errors.append(section.display_name)

    response_msg = _componse_response_msg(
        remove_success, \
        remove_errors, \
        publish_success, \
        publish_errors, \
        json.loads(request.body).get('publish')
    )

    return JsonResponse(data={
        "message": response_msg,
        "errors": {
            "publish_errors": publish_errors,
            "remove_errors": remove_errors,
        }
    }, status=status.HTTP_200_OK)



css_sanitizer = CSSSanitizer(allowed_css_properties=[])

all_html_tags = [
    'noscript','a','abbr','acronym','address','applet','area','article','aside','audio',
    'b','base','basefont','bdi','bdo','big','blockquote','body','br','button','canvas',
    'caption','center','cite','code','col','colgroup','data','datalist','dd','del','details',
    'dfn','dialog','dir','div','dl','dt','em','embed','fieldset','figcaption','figure','font',
    'footer','form','frame','frameset','h1','h2','h3','h4','h5','h6','head','header','hgroup',
    'img','input','ins','kbd','label','legend','li','link','main','map','mark','menu','meta',
    'meter','nav','noframes','noscript','object','ol','optgroup','option','output','p','param',
    'picture','pre','progress','q','rp','rt','ruby','s','samp','script','search','section','select',
    'small','source','span','strike','strong','style','sub','summary','sup','svg','table','tbody',
    'td','template','textarea','tfoot','th','thead','time','title','tr','track','tt','u','ul',
    'var','video','wbr','hr','html','i','iframe','o:p', 'v:shape', 'v:imagedata', 'v:shapetype', 
    'v:stroke', 'v:f', 'v:path', 'v:formulas', 'o:lock', 'w:borderright', 'w:bordertop', 'w:borderleft', 
    'w:borderbottom', 'google-sheets-html-origin'
]

tags_will_be_removed = []

def _allow_all_attrs_except_style(tag, name, value):
    return name != 'style'

def _remove_style(data):
    unescaped_data = html.unescape(data)
    for tag in tags_will_be_removed:
        unescaped_data = re.sub(tag, '', unescaped_data)

    cleaned_and_escaped_style_data = bleach.clean(unescaped_data, tags=all_html_tags, attributes=_allow_all_attrs_except_style)

    return cleaned_and_escaped_style_data

def _componse_response_msg(remove_success, remove_errors, publish_success, publish_errors, publish):
    response_msg = ""

    if len(remove_success) == 0 and len(remove_errors) == 0: 
        response_msg = "No remove styles actions happened. "
    
    elif len(remove_success) > 0 and len(remove_errors) == 0: 
        response_msg = "Successfully to remove styles on all components. "

    elif len(remove_success) == 0 and len(remove_errors) > 0: 
        response_msg = "Failed to remove styles on all components. "
    else: 
        response_msg = f"Failed to remove styles on {len(remove_errors)} component(s). "

    if publish:
        if len(publish_success) == 0 and len(publish_errors) == 0:
            response_msg += "No pulish actions happened."
        elif len(publish_success) > 0 and len(publish_errors) == 0:
            response_msg += "Published all sections successfully."
        elif len(publish_success) == 0 and len(publish_errors) > 0:
            response_msg += "Failed to publish all sections."
        else:
            response_msg += f"Failed to publish {len(publish_errors)} section(s)."
    else: 
        response_msg += "Did not publish."

    return response_msg