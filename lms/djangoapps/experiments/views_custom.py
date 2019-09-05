"""
The Discount API Views should return information about discounts that apply to the user and course.

"""
# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.utils.decorators import method_decorator
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace

from lms.djangoapps.experiments.utils import get_base_experiment_metadata_context
from student.models import CourseEnrollment
from course_modes.models import CourseMode




# .. feature_toggle_name: experiments.mobile_upsell_rev934
# .. feature_toggle_type: flag
# .. feature_toggle_default: False
# .. feature_toggle_description: Toggle mobile upsell enabled
# .. feature_toggle_category: experiments
# .. feature_toggle_use_cases: monitored_rollout
# .. feature_toggle_creation_date: 2019-09-05
# .. feature_toggle_expiration_date: None
# .. feature_toggle_warnings: None
# .. feature_toggle_tickets: REV-934
# .. feature_toggle_status: supported
MOBILE_UPSELL_FLAG = WaffleFlag(
    waffle_namespace=WaffleFlagNamespace(name=u'experiments'),
    flag_name=u'mobile_upsell_rev934',
    flag_undefined_default=False
)



class Rev934(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request discount information for a user and course

    **Example Requests**

        GET /api/discounts/v1/course/{course_key_string}

    **Response Values**

        Body consists of the following fields:
            discount_applicable:
                whether the user can receive a discount for this course
            jwt:
                the jwt with user information and discount information

        Response:
            {
            "show_upsell": true,
            "price": 49.00,
            "basket_url": "[https://ecommerce.edx.org/basket/add?sku=abcdef|https://ecommerce.edx.org/basket/add?sku=abcdef]"
            }

    **Parameters:**

        course_key_string:
            The course key for the which the discount should be applied

    **Returns**

        * 200 on success with above fields.
        * 401 if there is no user signed in.

        Example response:
        {
            "discount_applicable": false,
            "jwt": xxxxxxxx.xxxxxxxx.xxxxxxx
        }
    """
    authentication_classes = (JwtAuthentication, OAuth2AuthenticationAllowInactiveUser,
                              SessionAuthenticationAllowInactiveUser,)
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)

    # Since the course about page on the marketing site uses this API to auto-enroll users,
    # we need to support cross-domain CSRF.
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """
        Return the discount percent, if the user has appropriate permissions.
        """
        if not MOBILE_UPSELL_FLAG.is_enabled():
            return Response(
                {'show_upsell': False, 
                 'upsell_flag': False,
                }
            )

        course_id = request.GET.get('course_id').replace(' ', '+')
        course_key = CourseKey.from_string(course_id)
        course = CourseOverview.get_from_id(course_key)
        user = request.user


        enrollment = None
        user_enrollments = None
        audit_enrollments = None
        has_non_audit_enrollments = False
        try:
            user_enrollments = CourseEnrollment.objects.select_related('course').filter(user_id=user.id)
            has_non_audit_enrollments = user_enrollments.exclude(mode__in=CourseMode.UPSELL_TO_VERIFIED_MODES).exists()
            enrollment = CourseEnrollment.objects.select_related(
                'course'
            ).get(user_id=user.id, course_id=course.id)
        except CourseEnrollment.DoesNotExist:
            pass  # Not enrolled, use the default values

        context = get_base_experiment_metadata_context(course, user, enrollment, user_enrollments)
        
        return Response(
            {'show_upsell': True,
             'price': context.get('upgrade_price'),
             'basket_url': context.get('upgrade_link'),
            }
        )
