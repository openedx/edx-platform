"""
unit tests for course_info views and models.
"""
import json
from django.test.utils import override_settings

from contentstore.models import PushNotificationConfig
from contentstore.tests.test_course_settings import CourseTestCase
from contentstore.utils import reverse_course_url, reverse_usage_url
from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore

from student.tests.factories import CourseEnrollmentFactory, UserFactory
from edx_notifications.lib.consumer import get_notifications_count_for_user
from mock import patch


class CourseUpdateTest(CourseTestCase):
    """
    Test for course updates
    """
    def create_update_url(self, provided_id=None, course_key=None):
        if course_key is None:
            course_key = self.course.id
        kwargs = {'provided_id': str(provided_id)} if provided_id else None
        return reverse_course_url('course_info_update_handler', course_key, kwargs=kwargs)

    # The do all and end all of unit test cases.
    def test_course_update(self):
        """Go through each interface and ensure it works."""
        def get_response(content, date):
            """
            Helper method for making call to server and returning response.

            Does not supply a provided_id.
            """
            payload = {'content': content, 'date': date}
            url = self.create_update_url()

            resp = self.client.ajax_post(url, payload)
            self.assertContains(resp, '', status_code=200)

            return json.loads(resp.content)

        resp = self.client.get_html(
            reverse_course_url('course_info_handler', self.course.id)
        )
        self.assertContains(resp, 'Course Updates', status_code=200)

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'
        content = init_content + '</iframe>'
        payload = get_response(content, 'January 8, 2013')
        self.assertHTMLEqual(payload['content'], content)

        first_update_url = self.create_update_url(provided_id=payload['id'])
        content += '<div>div <p>p<br/></p></div>'
        payload['content'] = content
        # POST requests were coming in w/ these header values causing an error; so, repro error here
        resp = self.client.ajax_post(
            first_update_url, payload, HTTP_X_HTTP_METHOD_OVERRIDE="PUT", REQUEST_METHOD="POST"
        )

        self.assertHTMLEqual(content, json.loads(resp.content)['content'],
                             "iframe w/ div")
        # refetch using provided id
        refetched = self.client.get_json(first_update_url)
        self.assertHTMLEqual(
            content, json.loads(refetched.content)['content'], "get w/ provided id"
        )

        # now put in an evil update
        content = '<ol/>'
        payload = get_response(content, 'January 11, 2013')
        self.assertHTMLEqual(content, payload['content'], "self closing ol")

        course_update_url = self.create_update_url()
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == 2)

        # try json w/o required fields
        self.assertContains(
            self.client.ajax_post(course_update_url, {'garbage': 1}),
            'Failed to save', status_code=400
        )

        # test an update with text in the tail of the header
        content = 'outside <strong>inside</strong> after'
        payload = get_response(content, 'June 22, 2000')
        self.assertHTMLEqual(content, payload['content'], "text outside tag")

        # now try to update a non-existent update
        content = 'blah blah'
        payload = {'content': content, 'date': 'January 21, 2013'}
        self.assertContains(
            self.client.ajax_post(course_update_url + '9', payload),
            'Failed to save', status_code=400
        )

        # update w/ malformed html
        content = '<garbage tag No closing brace to force <span>error</span>'
        payload = {'content': content,
                   'date': 'January 11, 2013'}

        self.assertContains(
            self.client.ajax_post(course_update_url, payload),
            '<garbage'
        )

        # set to valid html which would break an xml parser
        content = "<p><br><br></p>"
        payload = get_response(content, 'January 11, 2013')
        self.assertHTMLEqual(content, payload['content'])

        # now try to delete a non-existent update
        self.assertContains(self.client.delete(course_update_url + '19'), "delete", status_code=400)

        # now delete a real update
        content = 'blah blah'
        payload = get_response(content, 'January 28, 2013')
        this_id = payload['id']
        self.assertHTMLEqual(content, payload['content'], "single iframe")
        # first count the entries
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        before_delete = len(payload)

        url = self.create_update_url(provided_id=this_id)
        resp = self.client.delete(url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == before_delete - 1)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_NOTIFICATIONS": True})
    def test_notifications_enabled_when_new_updates_in_course(self):
        # create new users and enroll them in the course.
        test_user_1 = UserFactory.create(password='test_pass')
        CourseEnrollmentFactory(user=test_user_1, course_id=self.course.id)
        test_user_2 = UserFactory.create(password='test_pass')
        CourseEnrollmentFactory(user=test_user_2, course_id=self.course.id)

        content = 'Test update'
        payload = {'content': content, 'date': 'Feb 19, 2015'}
        url = self.create_update_url()

        resp = self.client.ajax_post(
            url, payload, REQUEST_METHOD="POST"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertHTMLEqual(content, json.loads(resp.content)['content'])

        # now the enrolled users should get notification about the
        # course update where they are enrolled as student.
        self.assertTrue(get_notifications_count_for_user(test_user_1.id), 1)
        self.assertTrue(get_notifications_count_for_user(test_user_2.id), 1)

    def test_course_updates_compatibility(self):
        '''
        Test that course updates doesn't break on old data (content in 'data' field).
        Note: new data will save as list in 'items' field.
        '''
        # get the updates and populate 'data' field with some data.
        location = self.course.id.make_usage_key('course_info', 'updates')
        course_updates = modulestore().create_item(
            self.user.id,
            location.course_key,
            location.block_type,
            block_id=location.block_id
        )
        update_date = u"January 23, 2014"
        update_content = u"Hello world!"
        update_data = u"<ol><li><h2>" + update_date + "</h2>" + update_content + "</li></ol>"
        course_updates.data = update_data
        modulestore().update_item(course_updates, self.user.id)

        # test getting all updates list
        course_update_url = self.create_update_url()
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        self.assertEqual(payload, [{u'date': update_date, u'content': update_content, u'id': 1}])
        self.assertTrue(len(payload) == 1)

        # test getting single update item

        first_update_url = self.create_update_url(provided_id=payload[0]['id'])
        resp = self.client.get_json(first_update_url)
        payload = json.loads(resp.content)
        self.assertEqual(payload, {u'date': u'January 23, 2014', u'content': u'Hello world!', u'id': 1})
        self.assertHTMLEqual(update_date, payload['date'])
        self.assertHTMLEqual(update_content, payload['content'])

        # test that while updating it converts old data (with string format in 'data' field)
        # to new data (with list format in 'items' field) and respectively updates 'data' field.
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items, [])
        # now try to update first update item
        update_content = 'Testing'
        payload = {'content': update_content, 'date': update_date}
        resp = self.client.ajax_post(
            course_update_url + '1', payload, HTTP_X_HTTP_METHOD_OVERRIDE="PUT", REQUEST_METHOD="POST"
        )
        self.assertHTMLEqual(update_content, json.loads(resp.content)['content'])
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items, [{u'date': update_date, u'content': update_content, u'id': 1}])
        # course_updates 'data' field should not update automatically
        self.assertEqual(course_updates.data, '')

        # test delete course update item (soft delete)
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items, [{u'date': update_date, u'content': update_content, u'id': 1}])
        # now try to delete first update item
        resp = self.client.delete(course_update_url + '1')
        self.assertEqual(json.loads(resp.content), [])
        # confirm that course update is soft deleted ('status' flag set to 'deleted') in db
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items,
                         [{u'date': update_date, u'content': update_content, u'id': 1, u'status': 'deleted'}])

        # now try to get deleted update
        resp = self.client.get_json(course_update_url + '1')
        payload = json.loads(resp.content)
        self.assertEqual(payload.get('error'), u"Course update not found.")
        self.assertEqual(resp.status_code, 404)

        # now check that course update don't munges html
        update_content = u"""&lt;problem>
                           &lt;p>&lt;/p>
                           &lt;multiplechoiceresponse>
                           <pre>&lt;problem>
                               &lt;p>&lt;/p></pre>
                           <div><foo>bar</foo></div>"""
        payload = {'content': update_content, 'date': update_date}
        resp = self.client.ajax_post(
            course_update_url, payload, REQUEST_METHOD="POST"
        )
        self.assertHTMLEqual(update_content, json.loads(resp.content)['content'])

    def test_no_ol_course_update(self):
        '''Test trying to add to a saved course_update which is not an ol.'''
        # get the updates and set to something wrong
        location = self.course.id.make_usage_key('course_info', 'updates')
        modulestore().create_item(
            self.user.id,
            location.course_key,
            location.block_type,
            block_id=location.block_id
        )
        course_updates = modulestore().get_item(location)
        course_updates.data = 'bad news'
        modulestore().update_item(course_updates, self.user.id)

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'
        content = init_content + '</iframe>'
        payload = {'content': content, 'date': 'January 8, 2013'}

        course_update_url = self.create_update_url()
        resp = self.client.ajax_post(course_update_url, payload)

        payload = json.loads(resp.content)

        self.assertHTMLEqual(payload['content'], content)

        # now confirm that the bad news and the iframe make up single update
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == 1)

    def post_course_update(self, send_push_notification=False):
        """
        Posts an update to the course
        """
        course_update_url = self.create_update_url(course_key=self.course.id)

        # create a course via the view handler
        self.client.ajax_post(course_update_url)

        content = u"Sample update"
        payload = {'content': content, 'date': 'January 8, 2013'}
        if send_push_notification:
            payload['push_notification_selected'] = True
        resp = self.client.ajax_post(course_update_url, payload)

        # check that response status is 200 not 400
        self.assertEqual(resp.status_code, 200)

        payload = json.loads(resp.content)
        self.assertHTMLEqual(payload['content'], content)

    @patch("contentstore.push_notification.send_push_course_update")
    def test_post_course_update(self, mock_push_update):
        """
        Test that a user can successfully post on course updates and handouts of a course
        """
        self.post_course_update()

        # check that push notifications are not sent
        self.assertFalse(mock_push_update.called)

        updates_location = self.course.id.make_usage_key('course_info', 'updates')
        self.assertTrue(isinstance(updates_location, UsageKey))
        self.assertEqual(updates_location.name, u'updates')

        # check posting on handouts
        handouts_location = self.course.id.make_usage_key('course_info', 'handouts')
        course_handouts_url = reverse_usage_url('xblock_handler', handouts_location)

        content = u"Sample handout"
        payload = {'data': content}
        resp = self.client.ajax_post(course_handouts_url, payload)

        # check that response status is 200 not 500
        self.assertEqual(resp.status_code, 200)

        payload = json.loads(resp.content)
        self.assertHTMLEqual(payload['data'], content)

    @patch("contentstore.push_notification.send_push_course_update")
    def test_notifications_enabled_but_not_requested(self, mock_push_update):
        PushNotificationConfig(enabled=True).save()
        self.post_course_update()
        self.assertFalse(mock_push_update.called)

    @patch("contentstore.push_notification.send_push_course_update")
    def test_notifications_enabled_and_sent(self, mock_push_update):
        PushNotificationConfig(enabled=True).save()
        self.post_course_update(send_push_notification=True)
        self.assertTrue(mock_push_update.called)

    @override_settings(PARSE_KEYS={"APPLICATION_ID": "TEST_APPLICATION_ID", "REST_API_KEY": "TEST_REST_API_KEY"})
    @patch("contentstore.push_notification.Push")
    def test_notifications_sent_to_parse(self, mock_parse_push):
        PushNotificationConfig(enabled=True).save()
        self.post_course_update(send_push_notification=True)
        self.assertEquals(mock_parse_push.alert.call_count, 2)

    @override_settings(PARSE_KEYS={"APPLICATION_ID": "TEST_APPLICATION_ID", "REST_API_KEY": "TEST_REST_API_KEY"})
    @patch("contentstore.push_notification.log_exception")
    @patch("contentstore.push_notification.Push")
    def test_notifications_error_from_parse(self, mock_parse_push, mock_log_exception):
        PushNotificationConfig(enabled=True).save()
        from parse_rest.core import ParseError
        mock_parse_push.alert.side_effect = ParseError
        self.post_course_update(send_push_notification=True)
        self.assertTrue(mock_log_exception.called)
