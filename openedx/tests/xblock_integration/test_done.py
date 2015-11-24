"""
This tests that the completion XBlock correctly stores state. This
is a fairly simple XBlock, and a correspondingly simple test suite.
"""

import json
import mock
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory


class DoneEventTestMixin(object):
    """Mixin for easily verifying that events were emitted during a
    test. This code should not be reused outside of DoneXBlock and
    RateXBlock until we are much more comfortable with it. The
    preferred way to do this type of testing elsewhere in the platform
    is with the EventTestMixin defined in:
      common/djangoapps/util/testing.py

    For now, we are exploring how to build a test framework for
    XBlocks. This is production-quality code for use in one XBlock,
    but prototype-grade code for use generically. Once we have figured
    out what we're doing, hopefully in a few weeks, this should evolve
    become part of the generic XBlock testing framework
    (https://github.com/edx/edx-platform/pull/10831). I would like
    to build up a little bit of experience with it first in contexts
    like this one before abstracting it out.

    For abstracting this out, we would like to have better integration
    with existing event testing frameworks. This may mean porting code
    in one direction or the other.

    By design, we capture all events. We provide two functions:
    1. assert_no_events_were_emitted verifies that no events of a
       given search specification were emitted.
    2. assert_event_emitted verifies that an event of a given search
        specification was emitted.

    The Mongo/bok_choy event tests in cohorts have nice examplars for
    how such functionality might look.

    In the future, we would like to expand both search
    specifications. This is built in the edX event tracking acceptance
    tests, but is built on top of Mongo. We would also like to have
    nice error messages. This is in the edX event tracking tests, but
    would require a bit of work to tease out of the platform and make
    work in this context. We would also like to provide access to
    events for downstream consumers.

    There is a nice event test in bok_choy, but it has performance
    issues if used outside of acceptance testing (since it needs to
    spin up a browser).  There is also util.testing.EventTestMixin,
    but this is not very useful out-of-the-box.

    """
    def setUp(self):
        """
        We patch log_event to capture all events sent during the test.
        """
        def log_event(event):
            """
            A patch of log_event that just stores the event in the events list
            """
            self.events.append(event)

        super(DoneEventTestMixin, self).setUp()
        self.events = []
        patcher = mock.patch("track.views.log_event", log_event)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_no_events_were_emitted(self, event_type):
        """
        Ensures no events of a given type were emitted since the last event related assertion.

        We are relatively specific since things like implicit HTTP
        events almost always do get omitted, and new event types get
        added all the time. This is not useful without a filter.
        """
        for event in self.events:
            self.assertNotEqual(event['event_type'], event_type)

    def assert_event_emitted(self, event_type, event_fields=None):
        """
        Verify that an event was emitted with the given parameters.

        We can verify that specific event fields are set using the
        optional search parameter.
        """
        if not event_fields:
            event_fields = {}
        for event in self.events:
            if event['event_type'] == event_type:
                found = True
                for field in event_fields:
                    if field not in event['event']:
                        found = False
                    elif event_fields[field] != event['event'][field]:
                        found = False
                if found:
                    return
        self.assertIn({'event_type': event_type, 'event': event_fields}, self.events)

    def reset_tracker(self):
        """
        Reset the mock tracker in order to forget about old events.
        """
        self.events = []


class GradeEmissionTestMixin(object):
    '''
    This checks whether a grading event was correctly emitted. This puts basic
    plumbing in place, but we would like to:
    * Add search parameters. Is it for the right block? The right user? This
      only handles the case of one block/one user right now.
    * Check end-to-end. We would like to see grades in the database, not just
      look for emission. Looking for emission may still be helpful if there
      are multiple events in a test.

    This is a bit of work since we need to do a lot of translation
    between XBlock and edx-platform identifiers (e.g. url_name and
    usage key).
    '''
    def setUp(self):
        '''
        Hot-patch the grading emission system to capture grading events.
        '''
        def capture_score(user_id, usage_key, score, max_score):
            '''
            Hot-patch which stores scores in a local array instead of the
            database.

            Note that to make this generic, we'd need to do both.
            '''
            self.scores.append({'student': user_id,
                                'usage': usage_key,
                                'score': score,
                                'max_score': max_score})

        super(GradeEmissionTestMixin, self).setUp()

        self.scores = []
        patcher = mock.patch("courseware.module_render.set_score", capture_score)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_grade(self, grade):
        '''
        Confirm that the last grade set was equal to grade.

        In the future, this should take a user ID and a block url_name.
        '''
        self.assertEqual(grade, self.scores[-1]['score'])


class TestDone(DoneEventTestMixin, GradeEmissionTestMixin, SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Simple tests for the completion XBlock. We set up a page with two
    of the block, make sure the page renders, toggle them a few times,
    make sure they've toggled, and reconfirm the page renders.
    """
    STUDENTS = [
        {'email': 'view@test.com', 'password': 'foo'},
    ]

    @classmethod
    def setUpClass(cls):
        """
        Create a page with two of the XBlock on it
        """
        # Nose runs setUpClass methods even if a class decorator says to skip
        # the class: https://github.com/nose-devs/nose/issues/946
        # So, skip the test class here if we are not in the LMS.
        if settings.ROOT_URLCONF != 'lms.urls':
            raise unittest.SkipTest('Test only valid in lms')

        super(TestDone, cls).setUpClass()
        cls.course = CourseFactory.create(
            display_name='Done_Test_Course'
        )
        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                display_name='Overview',
                category='chapter'
            )
            cls.section = ItemFactory.create(
                parent=cls.chapter,
                display_name='Welcome',
                category='sequential'
            )
            cls.unit = ItemFactory.create(
                parent=cls.section,
                display_name='New Unit',
                category='vertical'
            )
            cls.xblock1 = ItemFactory.create(
                parent=cls.unit,
                category='done',
                display_name='done_0'
            )
            cls.xblock2 = ItemFactory.create(
                parent=cls.unit,
                category='done',
                display_name='done_1'
            )

        cls.course_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': unicode(cls.course.id),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )

    def setUp(self):
        """
        Create users
        """
        super(TestDone, self).setUp()
        for idx, student in enumerate(self.STUDENTS):
            username = "u{}".format(idx)
            self.create_account(username, student['email'], student['password'])
            self.activate_user(student['email'])

        self.staff_user = GlobalStaffFactory()

    def get_handler_url(self, handler, xblock_name=None):
        """
        Get url for the specified xblock handler
        """
        return reverse('xblock_handler', kwargs={
            'course_id': unicode(self.course.id),
            'usage_id': unicode(self.course.id.make_usage_key('done', xblock_name)),
            'handler': handler,
            'suffix': ''
        })

    def enroll_student(self, email, password):
        """
        Student login and enroll for the course
        """
        self.login(email, password)
        self.enroll(self.course, verify=True)

    def check_ajax(self, block, data, desired_state):
        """
        Make an AJAX call to the XBlock, and assert the state is as
        desired.
        """
        url = self.get_handler_url('toggle_button', 'done_' + str(block))
        resp = self.client.post(url, json.dumps(data), '')
        resp_data = json.loads(resp.content)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp_data, {"state": desired_state})
        return resp_data

    def test_done(self):
        """
        Walk through a few toggles. Make sure the blocks don't mix up
        state between them, initial state is correct, and final state
        is correct.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'])
        # We confirm we don't have errors rendering the student view
        self.assert_request_status_code(200, self.course_url)
        # We confirm the block is initially false
        self.check_ajax(0, {}, False)
        self.reset_tracker()
        self.check_ajax(1, {}, False)
        self.assert_no_events_were_emitted("edx.done.toggled")
        # We confirm we can toggle state both ways
        self.reset_tracker()
        self.check_ajax(0, {'done': True}, True)
        self.assert_event_emitted('edx.done.toggled', event_fields={"done": True})
        self.reset_tracker()
        self.check_ajax(1, {'done': False}, False)
        self.assert_event_emitted('edx.done.toggled', event_fields={"done": False})
        self.check_ajax(0, {'done': False}, False)
        self.assert_grade(0)
        self.check_ajax(1, {'done': True}, True)
        self.assert_grade(1)
        # We confirm state sticks around
        self.check_ajax(0, {}, False)
        self.check_ajax(1, {}, True)
        # We reconfirm we don't have errors rendering the student view
        self.assert_request_status_code(200, self.course_url)
        # Just a quick sanity check to make sure our tests are working...
        self.assert_request_status_code(404, "bad url")
