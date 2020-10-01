"""
Unit Tests for Course Card date views
"""
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from pyquery import PyQuery as pq

from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from openedx.features.course_card.helpers import get_course_open_date
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import CourseCard
from .helpers import save_course_custom_settings, set_course_dates

TEST_COURSE_OPEN_DATE = datetime.utcnow() + timedelta(days=1)


class CourseCardBaseClass(ModuleStoreTestCase):
    """
    Base class to setup test cases for Course Card date view
    """
    def setUp(self):
        super(CourseCardBaseClass, self).setUp()

        org = 'edX'
        course_number_f = 'CS101'
        course_run = '2015_Q1'
        display_name_f = 'test course 1'
        self.date_time_format = '%b %-d, %Y'
        self.about_page_date_time_format = '%B %d, %Y'

        self.course = CourseFactory.create(org=org, number=course_number_f, run=course_run,
                                           display_name=display_name_f,
                                           default_store=ModuleStoreEnum.Type.split,
                                           start=datetime.utcnow() - timedelta(days=30),
                                           end=datetime.utcnow() + timedelta(days=30))

        self.course.save()
        save_course_custom_settings(self.course.id, TEST_COURSE_OPEN_DATE)
        set_course_dates(self.course, -30, -10, -5, 30)
        CourseCard(course_id=self.course.id, course_name=self.course.display_name, is_enabled=True).save()

    @classmethod
    def setUpClass(cls):
        super(CourseCardBaseClass, cls).setUpClass()
        configure_philu_theme()


class CourseCardViewBaseClass(CourseCardBaseClass):
    """
       Contains the cases for course card date view
    """
    def test_catalog_course_date(self):
        response = self.client.get(reverse('courses'))
        # We are getting 3rd span from Div with class "course-date" and get text from it.
        # It cause a serious problem if CSS is changed. This need to checked if that happens.
        self.assertEqual(pq(response.content)("div.course-date > span")[2].text.strip(),
                         TEST_COURSE_OPEN_DATE.strftime(self.date_time_format))

    def test_about_course_date(self):
        response = self.client.get(reverse('about_course', args=[self.course.id]))
        # We are getting 1st para with class "start-date" and get text from it.
        # It cause a serious problem if CSS is changed. This need to checked if that happens.
        self.assertEqual(pq(response.content)("p.start-date")[0].text,
                         TEST_COURSE_OPEN_DATE.strftime(self.about_page_date_time_format))

    def test_coursecard_helper_course_open_date(self):
        course_start_date = get_course_open_date(self.course)
        self.assertEqual(course_start_date.strftime(self.date_time_format),
                         TEST_COURSE_OPEN_DATE.strftime(self.date_time_format))
