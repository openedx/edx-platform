from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr

from courseware.tests.tests import LoginEnrollmentTestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from mock import patch


@attr('shard_1')
class WikiRedirectTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for wiki course redirection.
    """

    def setUp(self):
        super(WikiRedirectTestCase, self).setUp()
        self.toy = CourseFactory.create(org='edX', course='toy', display_name='2012_Fall')

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        for username, email in [('u1', self.student), ('u2', self.instructor)]:
            self.create_account(username, email, self.password)
            self.activate_user(email)
            self.logout()

    @patch.dict("django.conf.settings.FEATURES", {'ALLOW_WIKI_ROOT_ACCESS': True})
    def test_wiki_redirect(self):
        """
        Test that requesting wiki URLs redirect properly to or out of classes.

        An enrolled in student going from /courses/edX/toy/2012_Fall/progress
        to /wiki/some/fake/wiki/page/ will redirect to
        /courses/edX/toy/2012_Fall/wiki/some/fake/wiki/page/

        An unenrolled student going to /courses/edX/toy/2012_Fall/wiki/some/fake/wiki/page/
        will be redirected to /wiki/some/fake/wiki/page/

        """
        self.login(self.student, self.password)

        self.enroll(self.toy)

        referer = reverse("progress", kwargs={'course_id': self.toy.id.to_deprecated_string()})
        destination = reverse("wiki:get", kwargs={'path': 'some/fake/wiki/page/'})

        redirected_to = referer.replace("progress", "wiki/some/fake/wiki/page/")

        resp = self.client.get(destination, HTTP_REFERER=referer)
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(resp['Location'], 'http://testserver' + redirected_to)

        # Now we test that the student will be redirected away from that page if the course doesn't exist
        # We do this in the same test because we want to make sure the redirected_to is constructed correctly
        # This is a location like /courses/*/wiki/* , but with an invalid course ID
        bad_course_wiki_page = redirected_to.replace(self.toy.location.course, "bad_course")

        resp = self.client.get(bad_course_wiki_page, HTTP_REFERER=referer)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver' + destination)

    @patch.dict("django.conf.settings.FEATURES", {'ALLOW_WIKI_ROOT_ACCESS': False})
    def test_wiki_no_root_access(self):
        """
        Test to verify that normally Wiki's cannot be browsed from the /wiki/xxxx/yyy/zz URLs

        """
        self.login(self.student, self.password)

        self.enroll(self.toy)

        referer = reverse("progress", kwargs={'course_id': self.toy.id.to_deprecated_string()})
        destination = reverse("wiki:get", kwargs={'path': 'some/fake/wiki/page/'})

        resp = self.client.get(destination, HTTP_REFERER=referer)
        self.assertEqual(resp.status_code, 403)

    def create_course_page(self, course):
        """
        Test that loading the course wiki page creates the wiki page.
        The user must be enrolled in the course to see the page.
        """

        course_wiki_home = reverse('course_wiki', kwargs={'course_id': course.id.to_deprecated_string()})
        referer = reverse("progress", kwargs={'course_id': self.toy.id.to_deprecated_string()})

        resp = self.client.get(course_wiki_home, follow=True, HTTP_REFERER=referer)

        course_wiki_page = referer.replace('progress', 'wiki/' + self.toy.wiki_slug + "/")

        ending_location = resp.redirect_chain[-1][0]

        self.assertEquals(ending_location, 'http://testserver' + course_wiki_page)
        self.assertEquals(resp.status_code, 200)

        self.has_course_navigator(resp)

    def has_course_navigator(self, resp):
        """
        Ensure that the response has the course navigator.
        """
        self.assertContains(resp, "Home")
        self.assertContains(resp, "Course")

    @patch.dict("django.conf.settings.FEATURES", {'ALLOW_WIKI_ROOT_ACCESS': True})
    def test_course_navigator(self):
        """"
        Test that going from a course page to a wiki page contains the course navigator.
        """

        self.login(self.student, self.password)
        self.enroll(self.toy)
        self.create_course_page(self.toy)

        course_wiki_page = reverse('wiki:get', kwargs={'path': self.toy.wiki_slug + '/'})
        referer = reverse("courseware", kwargs={'course_id': self.toy.id.to_deprecated_string()})

        resp = self.client.get(course_wiki_page, follow=True, HTTP_REFERER=referer)

        self.has_course_navigator(resp)

    @patch.dict("django.conf.settings.FEATURES", {'ALLOW_WIKI_ROOT_ACCESS': True})
    def test_wiki_not_accessible_when_not_enrolled(self):
        """
        Test that going from a course page to a wiki page when not enrolled
        redirects a user to the course about page
        """

        self.login(self.instructor, self.password)
        self.enroll(self.toy)
        self.create_course_page(self.toy)
        self.logout()

        self.login(self.student, self.password)
        course_wiki_page = reverse('wiki:get', kwargs={'path': self.toy.wiki_slug + '/'})
        referer = reverse("courseware", kwargs={'course_id': self.toy.id.to_deprecated_string()})

        # When not enrolled, we should get a 302
        resp = self.client.get(course_wiki_page, follow=False, HTTP_REFERER=referer)
        self.assertEqual(resp.status_code, 302)

        # and end up at the course about page
        resp = self.client.get(course_wiki_page, follow=True, HTTP_REFERER=referer)
        target_url, __ = resp.redirect_chain[-1]
        self.assertTrue(
            target_url.endswith(reverse('about_course', args=[self.toy.id.to_deprecated_string()]))
        )

    @patch.dict("django.conf.settings.FEATURES", {'ALLOW_WIKI_ROOT_ACCESS': True})
    def test_redirect_when_not_logged_in(self):
        """
        Test that attempting to reach a course wiki page when not logged in
        redirects the user to the login page
        """
        self.logout()
        course_wiki_page = reverse('wiki:get', kwargs={'path': self.toy.wiki_slug + '/'})

        # When not logged in, we should get a 302
        resp = self.client.get(course_wiki_page, follow=False)
        self.assertEqual(resp.status_code, 302)

        # and end up at the login page
        resp = self.client.get(course_wiki_page, follow=True)
        target_url, __ = resp.redirect_chain[-1]
        self.assertTrue(reverse('signin_user') in target_url)
