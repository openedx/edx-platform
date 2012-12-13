from django.test.testcases import TestCase
import datetime
import time
from django.contrib.auth.models import User
import xmodule
from django.test.client import Client
from django.core.urlresolvers import reverse
from xmodule.modulestore import Location
from cms.djangoapps.models.settings.course_details import CourseDetails,\
    CourseSettingsEncoder
import json
from util import converters
import calendar

# YYYY-MM-DDThh:mm:ss.s+/-HH:MM
class ConvertersTestCase(TestCase):
    def struct_to_datetime(self, struct_time):
        return datetime.datetime(struct_time.tm_year, struct_time.tm_mon, struct_time.tm_mday, struct_time.tm_hour, struct_time.tm_min, struct_time.tm_sec)
        
    def compare_dates(self, date1, date2, expected_delta):
        dt1 = self.struct_to_datetime(date1)
        dt2 = self.struct_to_datetime(date2)
        self.assertEqual(dt1 - dt2, expected_delta, str(date1) + "-" + str(date2) + "!=" + str(expected_delta))
        
    def test_iso_to_struct(self):
        self.compare_dates(converters.jsdate_to_time("2013-01-01"), converters.jsdate_to_time("2012-12-31"), datetime.timedelta(days=1))
        self.compare_dates(converters.jsdate_to_time("2013-01-01T00"), converters.jsdate_to_time("2012-12-31T23"), datetime.timedelta(hours=1))
        self.compare_dates(converters.jsdate_to_time("2013-01-01T00:00"), converters.jsdate_to_time("2012-12-31T23:59"), datetime.timedelta(minutes=1))
        self.compare_dates(converters.jsdate_to_time("2013-01-01T00:00:00"), converters.jsdate_to_time("2012-12-31T23:59:59"), datetime.timedelta(seconds=1))
    
class CourseDetailsTestCase(TestCase):
    def setUp(self):
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        xmodule.templates.update_templates()

        self.client = Client()
        self.client.login(username=uname, password=password)

        self.course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            }
        self.course_location = Location('i4x', 'MITx', '999', 'course', 'Robot_Super_Course')
        self.create_course()

    def tearDown(self):
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

    def create_course(self):
        """Create new course"""
        self.client.post(reverse('create_new_course'), self.course_data)

    def test_virgin_fetch(self):
        details = CourseDetails.fetch(self.course_location)
        self.assertEqual(details.course_location, self.course_location, "Location not copied into")
        self.assertIsNone(details.end_date, "end date somehow initialized " + str(details.end_date))
        self.assertIsNone(details.enrollment_start, "enrollment_start date somehow initialized " + str(details.enrollment_start))
        self.assertIsNone(details.enrollment_end, "enrollment_end date somehow initialized " + str(details.enrollment_end))
        self.assertIsNone(details.syllabus, "syllabus somehow initialized" + str(details.syllabus))
        self.assertEqual(details.overview, "", "overview somehow initialized" + details.overview)
        self.assertIsNone(details.intro_video, "intro_video somehow initialized" + str(details.intro_video))
        self.assertIsNone(details.effort, "effort somehow initialized" + str(details.effort))
        
    def test_encoder(self):
        details = CourseDetails.fetch(self.course_location)
        jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        jsondetails = json.loads(jsondetails)
        self.assertTupleEqual(Location(jsondetails['course_location']), self.course_location, "Location !=")
        # Note, start_date is being initialized someplace. I'm not sure why b/c the default will make no sense.
        self.assertIsNone(jsondetails['end_date'], "end date somehow initialized ")
        self.assertIsNone(jsondetails['enrollment_start'], "enrollment_start date somehow initialized ")
        self.assertIsNone(jsondetails['enrollment_end'], "enrollment_end date somehow initialized ")
        self.assertIsNone(jsondetails['syllabus'], "syllabus somehow initialized")
        self.assertEqual(jsondetails['overview'], "", "overview somehow initialized")
        self.assertIsNone(jsondetails['intro_video'], "intro_video somehow initialized")
        self.assertIsNone(jsondetails['effort'], "effort somehow initialized")
        
    def test_update_and_fetch(self):
        ## NOTE: I couldn't figure out how to validly test time setting w/ all the conversions
        jsondetails = CourseDetails.fetch(self.course_location)
        jsondetails.syllabus = "<a href='foo'>bar</a>"
        self.assertEqual(CourseDetails.update_from_json(jsondetails.__dict__).syllabus,
                             jsondetails.syllabus, "After set syllabus")
        jsondetails.overview = "Overview"
        self.assertEqual(CourseDetails.update_from_json(jsondetails.__dict__).overview,
                             jsondetails.overview, "After set overview")
        jsondetails.intro_video = "intro_video"
        self.assertEqual(CourseDetails.update_from_json(jsondetails.__dict__).intro_video,
                             jsondetails.intro_video, "After set intro_video")
        jsondetails.effort = "effort"
        self.assertEqual(CourseDetails.update_from_json(jsondetails.__dict__).effort,
                             jsondetails.effort, "After set effort")

class CourseDetailsViewTest(TestCase):
    def setUp(self):
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        xmodule.templates.update_templates()

        self.client = Client()
        self.client.login(username=uname, password=password)

        self.course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            }
        self.course_location = Location('i4x', 'MITx', '999', 'course', 'Robot_Super_Course')
        self.create_course()

    def tearDown(self):
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

    def create_course(self):
        """Create new course"""
        self.client.post(reverse('create_new_course'), self.course_data)

    def alter_field(self, url, details, field, val):
        setattr(details, field, val)
#        jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        resp = self.client.post(url, details) 
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, field + val)
        
    def test_update_and_fetch(self):
        details = CourseDetails.fetch(self.course_location)
        
        resp = self.client.get(reverse('course_settings', kwargs={'org' : self.course_location.org, 'course' : self.course_location.course, 
                                                                  'name' : self.course_location.name }))
        self.assertContains(resp, '<li><a href="#" class="is-shown" data-section="details">Course Details</a></li>', status_code=200, html=True)

        # resp s/b json from here on    
        url = reverse('course_settings', kwargs={'org' : self.course_location.org, 'course' : self.course_location.course, 
                                                 'name' : self.course_location.name, 'section' : 'details' })
        resp = self.client.get(url)
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, "virgin get")

#        self.alter_field(url, details, 'start_date', time.time() * 1000)        
#        self.alter_field(url, details, 'start_date', time.time() * 1000 + 60 * 60 * 24)
#        self.alter_field(url, details, 'end_date', time.time() * 1000 + 60 * 60 * 24 * 100)
#        self.alter_field(url, details, 'enrollment_start', time.time() * 1000)
#
#        self.alter_field(url, details, 'enrollment_end', time.time() * 1000 + 60 * 60 * 24 * 8)
#        self.alter_field(url, details, 'syllabus', "<a href='foo'>bar</a>")
#        self.alter_field(url, details, 'overview', "Overview")
#        self.alter_field(url, details, 'intro_video', "intro_video")
#        self.alter_field(url, details, 'effort', "effort")

    def compare_details_with_encoding(self, encoded, details, context):
        self.compare_date_fields(details, encoded, context, 'start_date')
        self.compare_date_fields(details, encoded, context, 'end_date')
        self.compare_date_fields(details, encoded, context, 'enrollment_start')
        self.compare_date_fields(details, encoded, context, 'enrollment_end')
        self.assertEqual(details['overview'], encoded['overview'], context + " overviews not ==")
        self.assertEqual(details['intro_video'], encoded.get('intro_video', None), context + " intro_video not ==")
        self.assertEqual(details['effort'], encoded['effort'], context + " efforts not ==")
        
    def compare_date_fields(self, details, encoded, context, field):
        if details[field] is not None:
            if field in encoded and encoded[field] is not None:
                self.assertEqual(encoded[field] / 1000, calendar.timegm(details[field]), "dates not == at " + context)
            else:
                self.fail(field + " missing from encoded but in details at " + context)
        elif field in encoded and encoded[field] is not None:
            self.fail(field + " included in encoding but missing from details at " + context)
        