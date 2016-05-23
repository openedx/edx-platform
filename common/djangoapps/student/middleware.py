"""
Middleware that checks user standing for the purpose of keeping users with
disabled accounts from accessing the site.
"""
import re
from django.conf import settings

from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.conf import settings
from student.models import UserStanding
from organizations.models import Organization

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey

COURSE_REGEX = re.compile(r'^.*?/course/{}'.format(settings.COURSE_ID_PATTERN))

class UserStandingMiddleware(object):
    """
    Checks a user's standing on request. Returns a 403 if the user's
    status is 'disabled'.
    """
    def process_request(self, request):
        user = request.user
        try:
            user_account = UserStanding.objects.get(user=user.id)
            # because user is a unique field in UserStanding, there will either be
            # one or zero user_accounts associated with a UserStanding
        except UserStanding.DoesNotExist:
            pass
        else:
            if user_account.account_status == UserStanding.ACCOUNT_DISABLED:
                msg = _(
                    'Your account has been disabled. If you believe '
                    'this was done in error, please contact us at '
                    '{support_email}'
                ).format(
                    support_email=u'<a href="mailto:{address}?subject={subject_line}">{address}</a>'.format(
                        address=settings.DEFAULT_FEEDBACK_EMAIL,
                        subject_line=_('Disabled Account'),
                    ),
                )
                return HttpResponseForbidden(msg)


class UserCourseFilteringMiddleware(object):
    """
    Checks that a user does in fact belong to the course ORG they are requesting
    to view/edit. Returns a 403 if the user does not belong to the same ORG.
    """
    def process_request(self, request):
        user = request.user

        user_org = Organization.objects.filter(
            organizationuser__active=True,
            organizationuser__user_id_id=user.id).values().first()

        u_org_id = user_org['id'] if user_org else None

	def course_id_from_url(url):
	    """
	    Extracts the course_id from the given `url`.
	    """
	    if not url:
		return None

	    match = COURSE_REGEX.match(url)

	    if match is None:
		return None

	    course_id = match.group('course_id')

	    if course_id is None:
		return None

	    try:
		return SlashSeparatedCourseKey.from_deprecated_string(course_id)
	    except InvalidKeyError:
		return None

        course_id = course_id_from_url(request.path)
        course_org = Organization.objects.filter(
            organizationcourse__course_id=course_id).values().first()

        c_org_id = course_org['id'] if course_org else None

        if u_org_id and c_org_id:
          if not c_org_id == u_org_id:
              msg = _('You do not belong to this organization. '
                'If you believe this is an error, please '
                'contact us at {support_email}'
              ).format(
                support_email=u'<a href="mailto:{address}?subject={subject_line}">{address}</a>'.format(
                    address=settings.DEFAULT_FEEDBACK_EMAIL,
                    subject_line=_('User Organization Incorrect'),
                ),
              )
              return HttpResponseForbidden(msg)
