"""
Tests labster course license views
"""
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore
from student.tests.factories import AdminFactory
from ccx.tests.factories import CcxFactory
from ccx_keys.locator import CCXLocator
from labster_course_license.views import set_license


class TestSetLicense(ModuleStoreTestCase):
    """
    Tests for set_license method.
    """
    def setUp(self):
        super(TestSetLicense, self).setUp()
        self.course = CourseFactory.create()
        self.ccx = CcxFactory.create(course_id=self.course.id)
        self.request_factory = RequestFactory()
        self.instructor = AdminFactory.create()
        self.license = 'YildVfefwmrTwNPPeapcNrugbkyb34sFoKiolPtk'
        self.store = modulestore()

    def create_valid_simulations(self):
        """
        Return list of simulations with valid parameters.
        """
        return [ItemFactory.create(
            category='lti',
            modulestore=self.store,
            display_name='LTI%d' % cnt
        ) for cnt in range(5)]

    def test_valid_simulation_ids(self):
        request = self.request_factory.post(
            reverse("labster_license_handler"),
            data={'license': self.license, 'update': True}
        )
        request.user = self.instructor
        self.create_valid_simulations()
        res = set_license(request, self.course, self.ccx)
        messages = res.context.get('messages')[0]
        ccx_locator = CCXLocator.from_course_locator(self.course.id, self.ccx.id)
        url = reverse('labster_license_handler', kwargs={'course_id': ccx_locator})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, url)
