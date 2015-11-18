"""Middleware for course_wiki"""
from urlparse import urlparse
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from wiki.models import reverse

from courseware.courses import get_course_with_access
from courseware.access import has_access
from student.models import CourseEnrollment
from util.request import course_id_from_url


class WikiAccessMiddleware(object):
    """
    This middleware wraps calls to django-wiki in order to handle authentication and redirection
    between the root wiki and the course wikis.

    TODO: removing the "root wiki" would obviate the need for this middleware; it could be replaced
          with a wrapper function around the wiki views. This is currently difficult or impossible to do
          because there are two sets of wiki urls loaded in urls.py
    """
    def _redirect_from_referrer(self, request, wiki_path):
        """
        redirect to course wiki url if the referrer is from a course page
        """
        course_id = course_id_from_url(request.META.get('HTTP_REFERER'))
        if course_id:
            # See if we are able to view the course. If we are, redirect to it
            try:
                _course = get_course_with_access(request.user, 'load', course_id)
                return redirect("/courses/{course_id}/wiki/{path}".format(course_id=course_id.to_deprecated_string(), path=wiki_path))
            except Http404:
                # Even though we came from the course, we can't see it. So don't worry about it.
                pass

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        This function handles authentication logic for wiki urls and redirects from
        the "root wiki" to the "course wiki" if the user accesses the wiki from a course url
        """
        # we care only about requests to wiki urls
        if not view_func.__module__.startswith('wiki.'):
            return

        # wiki pages are login required
        if not request.user.is_authenticated():
            return redirect(reverse('signin_user'), next=request.path)

        course_id = course_id_from_url(request.path)
        wiki_path = request.path.partition('/wiki/')[2]

        if course_id:
            # This is a /courses/org/name/run/wiki request
            course_path = "/courses/{}".format(course_id.to_deprecated_string())
            # HACK: django-wiki monkeypatches the reverse function to enable
            # urls to be rewritten
            reverse._transform_url = lambda url: course_path + url  # pylint: disable=protected-access
            # Authorization Check
            # Let's see if user is enrolled or the course allows for public access
            try:
                course = get_course_with_access(request.user, 'load', course_id)
            except Http404:
                # course does not exist. redirect to root wiki.
                # clearing the referrer will cause process_response not to redirect
                # back to a non-existent course
                request.META['HTTP_REFERER'] = ''
                return redirect('/wiki/{}'.format(wiki_path))

            if not course.allow_public_wiki_access:
                is_enrolled = CourseEnrollment.is_enrolled(request.user, course.id)
                is_staff = has_access(request.user, 'staff', course)
                if not (is_enrolled or is_staff):
                    # if a user is logged in, but not authorized to see a page,
                    # we'll redirect them to the course about page
                    return redirect('about_course', course_id.to_deprecated_string())
            # set the course onto here so that the wiki template can show the course navigation
            request.course = course
        else:
            # this is a request for /wiki/...

            # Check to see if we don't allow top-level access to the wiki via the /wiki/xxxx/yyy/zzz URLs
            # this will help prevent people from writing pell-mell to the Wiki in an unstructured way
            if not settings.FEATURES.get('ALLOW_WIKI_ROOT_ACCESS', False):
                raise PermissionDenied()

            return self._redirect_from_referrer(request, wiki_path)

    def process_response(self, request, response):
        """
        Modify the redirect from /wiki/123 to /course/foo/bar/wiki/123/
        if the referrer comes from a course page
        """
        if response.status_code == 302 and response['Location'].startswith('/wiki/'):
            wiki_path = urlparse(response['Location']).path.split('/wiki/', 1)[1]

            response = self._redirect_from_referrer(request, wiki_path) or response

        # END HACK: _transform_url must be set to a no-op function after it's done its work
        reverse._transform_url = lambda url: url  # pylint: disable=protected-access
        return response
