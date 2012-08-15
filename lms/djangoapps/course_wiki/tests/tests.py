from django.core.urlresolvers import reverse
from override_settings import override_settings

import xmodule.modulestore.django

from courseware.tests.tests import PageLoader, TEST_DATA_XML_MODULESTORE
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_from_xml


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class WikiRedirectTestCase(PageLoader):
    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()
        
        def find_course(name):
            """Assumes the course is present"""
            return [c for c in courses if c.location.course==name][0]

        self.full = find_course("full")
        self.toy = find_course("toy")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)
        
    
    
    def test_wiki_redirect(self):
        """
        Test that an enrolled in student going from /courses/edX/toy/2012_Fall/profile 
        to /wiki/some/fake/wiki/page/ will redirect to 
        /courses/edX/toy/2012_Fall/wiki/some/fake/wiki/page/
        
        Test that an unenrolled student going to /courses/edX/toy/2012_Fall/wiki/some/fake/wiki/page/
        will be redirected to /wiki/some/fake/wiki/page/
        
        """
        self.login(self.student, self.password)
        
        self.enroll(self.toy)
        
        referer = reverse("profile", kwargs={ 'course_id' : self.toy.id })
        destination = reverse("wiki:get", kwargs={'path': 'some/fake/wiki/page/'})
        
        redirected_to = referer.replace("profile", "wiki/some/fake/wiki/page/")
        
        resp = self.client.get( destination, HTTP_REFERER=referer)
        self.assertEqual(resp.status_code, 302 )
        
        self.assertEqual(resp['Location'], 'http://testserver' + redirected_to )
        
        
        # Now we test that the student will be redirected away from that page if they are unenrolled
        # We do this in the same test because we want to make sure the redirected_to is the same
        
        self.unenroll(self.toy)
        
        resp = self.client.get( redirected_to, HTTP_REFERER=referer)
        print "redirected_to" , redirected_to
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver' + destination )
        
        
        
        
