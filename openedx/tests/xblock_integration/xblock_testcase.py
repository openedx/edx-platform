"""This file defines a testing framework for XBlocks. This framework
is designed to be independent of the edx-platform, to allow:

1. The tests to move into the XBlock repositories.
2. The tests to work in xblock-sdk and other runtimes.

This is a prototype. We reserve the right to change the APIs at any
point, and expect to do so a few times before freezing.

At this point, we support:

1. Python unit testing
2. Event publish testing
3. Testing multiple students
4. Testing multiple XBloccks on the same page.

We have spec'ed out how to do acceptance testing, but have not
implemented itt yet. We have not spec'ed out JavaScript testing,
but believe it is important.

We do not intend to spec out XBlock/edx-platform integration testing
in the immediate future. This is best built as traditional
edx-platform tests for now.

We also do not plan to work on regression testing (taking live data
and replaying it) for now, but also believe it is important to do so
either in this framework or another.

Our next steps would be to:
* Finish this framework
* Move tests into the XBlocks themselves
* Run tests via entrypoints
  - Have an appropriate test to make sure those tests are likely
    running for standard XBlocks (e.g. assert those entry points
    exist)
"""

import collections
import json
import mock
import unittest

from xblock.plugin import Plugin

from django.conf import settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase

import lms.djangoapps.lms_xblock.runtime


class XBlockEventTestMixin(object):
    """Mixin for easily verifying that events were published during a
    test.

    To do:
    * Evaluate patching runtime.emit instead of log_event
    * Evaluate using @mulby's event compare library

    By design, we capture all published events. We provide two functions:
    1. assert_no_events_published verifies that no events of a
       given search specification were published.
    2. assert_event_published verifies that an event of a given search
        specification was published.

    The Mongo/bok_choy event tests in cohorts have nice examplars for
    how such functionality might look.

    In the future, we would like to expand both search
    specifications. This is built in the edX event tracking acceptance
    tests, but is built on top of Mongo. We would also like to have
    nice error messages. This is in the edX event tracking tests, but
    would require a bit of work to tease out of the platform and make
    work in this context. We would also like to provide access to
    events for downstream consumers.

    Good things to look at as developing the code:
    * Gabe's library for parsing events. This is nice.
    * Bok choy has a nice Mongo search for events in the cohorts test
      case. It is a little slow for the general case.
    * This is originally based on a cleanup of the EventTestMixin. We
      could work to converge those in some sensible way.
    """
    def setUp(self):
        """
        We patch runtime.publish to capture all XBlock events sent during the test.

        This is a little bit ugly -- it's all dynamic -- so we patch __init__ for the
        system runtime to capture the dynamically-created publish, and catch whatever
        is being passed into it.
        """
        saved_init = lms.djangoapps.lms_xblock.runtime.LmsModuleSystem.__init__

        def patched_init(runtime_self, **kwargs):
            """
            Swap out publish in the __init__
            """
            old_publish = kwargs["publish"]

            def publish(block, event_type, event):
                """
                Log the event, and call the original publish
                """
                self.events.append({"event": event, "event_type": event_type})
                old_publish(block, event_type, event)
            kwargs['publish'] = publish
            return saved_init(runtime_self, **kwargs)

        super(XBlockEventTestMixin, self).setUp()
        self.events = []
        patcher = mock.patch("lms.djangoapps.lms_xblock.runtime.LmsModuleSystem.__init__", patched_init)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_no_events_published(self, event_type):
        """
        Ensures no events of a given type were published since the last event related assertion.

        We are relatively specific since things like implicit HTTP
        events almost always do get omitted, and new event types get
        added all the time. This is not useful without a filter.
        """
        for event in self.events:
            self.assertNotEqual(event['event_type'], event_type)

    def assert_event_published(self, event_type, event_fields=None):
        """
        Verify that an event was published with the given parameters.

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

    def reset_published_events(self):
        """
        Reset the mock tracker in order to forget about old events.
        """
        self.events = []


class GradePublishTestMixin(object):
    '''
    This checks whether a grading event was correctly published. This puts basic
    plumbing in place, but we would like to:
    * Add search parameters. Is it for the right block? The right user? This
      only handles the case of one block/one user right now.
    * Check end-to-end. We would like to see grades in the database, not just
      look for emission. Looking for emission may still be helpful if there
      are multiple events in a test.

    This is a bit of work since we need to do a lot of translation
    between XBlock and edx-platform identifiers (e.g. url_name and
    usage key).

    We could also use the runtime.publish logic above, now that we have it.
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

        super(GradePublishTestMixin, self).setUp()

        self.scores = []
        patcher = mock.patch("courseware.module_render.set_score", capture_score)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_grade(self, grade):
        '''
        Confirm that the last grade set was equal to grade.

        HACK: In the future, this should take a user ID and a block url_name.
        '''
        self.assertEqual(grade, self.scores[-1]['score'])


class XBlockScenarioTestCaseMixin(object):
    '''
    This allows us to have test cases defined in JSON today, and in OLX
    someday.
    '''
    @classmethod
    def setUpClass(cls):
        """
        Create a page with two of the XBlock on it
        """
        super(XBlockScenarioTestCaseMixin, cls).setUpClass()

        cls.course = CourseFactory.create(
            display_name='XBlock_Test_Course'
        )
        cls.scenario_urls = {}
        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            for chapter_config in cls.test_configuration:
                chapter = ItemFactory.create(
                    parent=cls.course,
                    display_name="ch_" + chapter_config['urlname'],
                    category='chapter'
                )
                section = ItemFactory.create(
                    parent=chapter,
                    display_name="sec_" + chapter_config['urlname'],
                    category='sequential'
                )
                unit = ItemFactory.create(
                    parent=section,
                    display_name='New Unit',
                    category='vertical'
                )
                for xblock_config in chapter_config['xblocks']:
                    ItemFactory.create(
                        parent=unit,
                        category=xblock_config['blocktype'],
                        display_name=xblock_config['urlname']
                    )

                scenario_url = unicode(reverse(
                    'courseware_section',
                    kwargs={
                        'course_id': unicode(cls.course.id),
                        'chapter': "ch_" + chapter_config['urlname'],
                        'section': "sec_" + chapter_config['urlname']
                    }
                ))

                cls.scenario_urls[chapter_config['urlname']] = scenario_url


class XBlockStudentTestCaseMixin(object):
    '''
    Creates a default set of students for XBlock tests
    '''
    student_list = [
        {'email': 'alice@test.edx.org', 'password': 'foo'},
        {'email': 'bob@test.edx.org', 'password': 'foo'},
        {'email': 'eve@test.edx.org', 'password': 'foo'},
    ]

    def setUp(self):
        """
        Create users accounts. The first three, we give helpful names to. If
        there are any more, we auto-generate number IDs. We intentionally use
        slightly different conventions for different users, so we exercise
        more corner cases, but we could standardize if this is more hassle than
        it's worth.
        """
        super(XBlockStudentTestCaseMixin, self).setUp()
        for idx, student in enumerate(self.student_list):
            username = "u{}".format(idx)
            self._enroll_user(username, student['email'], student['password'])
        self.select_student(0)

    def _enroll_user(self, username, email, password):
        '''
        Create and activate a user account.
        '''
        self.create_account(username, email, password)
        self.activate_user(email)

    def select_student(self, user_id):
        """
        Select a current user account
        """
        # If we don't have enough users, add a few more...
        for user_id in range(len(self.student_list), user_id):
            username = "user_{i}".format(i=user_id)
            email = "user_{i}@example.edx.org".format(i=user_id)
            password = "12345"
            self._enroll_user(username, email, password)
            self.student_list.append({'email': email, 'password': password})

        email = self.student_list[user_id]['email']
        password = self.student_list[user_id]['password']

        # ... and log in as the appropriate user
        self.login(email, password)
        self.enroll(self.course, verify=True)


class XBlockTestCase(XBlockStudentTestCaseMixin,
                     XBlockScenarioTestCaseMixin,
                     XBlockEventTestMixin,
                     GradePublishTestMixin,
                     SharedModuleStoreTestCase,
                     LoginEnrollmentTestCase,
                     Plugin):
    """
    Class for all XBlock-internal test cases (as opposed to integration tests).
    """
    test_configuration = None  # Children must override this!

    entry_point = 'xblock.test.v0'

    @classmethod
    def setUpClass(cls):
        '''
        Unless overridden, we create two student users and one staff
        user. We create the course hierarchy based on the OLX defined
        in the XBlock test class. Until we can deal with OLX, that
        actually will come from a list.
        '''
        # Nose runs setUpClass methods even if a class decorator says to skip
        # the class: https://github.com/nose-devs/nose/issues/946
        # So, skip the test class here if we are not in the LMS.
        if settings.ROOT_URLCONF != 'lms.urls':
            raise unittest.SkipTest('Test only valid in lms')

        super(XBlockTestCase, cls).setUpClass()

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

    def ajax(self, function, block_urlname, json_data):
        '''
        Call a json_handler in the XBlock. Return the response as
        an object containing response code and JSON.
        '''
        url = self._get_handler_url(function, block_urlname)
        resp = self.client.post(url, json.dumps(json_data), '')
        ajax_response = collections.namedtuple('AjaxResponse',
                                               ['data', 'status_code'])
        ajax_response.data = json.loads(resp.content)
        ajax_response.status_code = resp.status_code
        return ajax_response

    def _get_handler_url(self, handler, xblock_name=None):
        """
        Get url for the specified xblock handler
        """
        xblock_type = None
        for scenario in self.test_configuration:
            for block in scenario["xblocks"]:
                if block["urlname"] == xblock_name:
                    xblock_type = block["blocktype"]

        key = unicode(self.course.id.make_usage_key(xblock_type, xblock_name))

        return reverse('xblock_handler', kwargs={
            'course_id': unicode(self.course.id),
            'usage_id': key,
            'handler': handler,
            'suffix': ''
        })

    def render_block(self, block_urlname):
        '''
        Return a rendering of the XBlock.

        We should include data, but with a selector dropping
        the rest of the HTML around the block.

        To do: Implement returning the XBlock's HTML. This is an XML
        selector on the returned response for that div.
        '''
        section = self._containing_section(block_urlname)
        html_response = collections.namedtuple('HtmlResponse',
                                               ['status_code'])
        url = self.scenario_urls[section]
        response = self.client.get(url)
        html_response.status_code = response.status_code
        return html_response

    def _containing_section(self, block_urlname):
        '''
        For a given block, return the parent section
        '''
        for section in self.test_configuration:
            blocks = section["xblocks"]
            for block in blocks:
                if block['urlname'] == block_urlname:
                    return section['urlname']
        raise Exception("Block not found " + block_urlname)

    def assertXBlockScreenshot(self, block_urlname, rendering=None):
        '''
        As in Bok Choi, but instead of a CSS selector, we pass a
        block_id. We may want to be able to pass an optional selector
        for picking a subelement of the block.

        This confirms status code, and that the screenshot is
        identical.

        To do: Implement
        '''
        raise NotImplementedError("We need Ben's help to finish this")
