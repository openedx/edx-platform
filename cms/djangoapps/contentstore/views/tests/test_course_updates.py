"""
unit tests for course_info views and models.
"""


import json
from opaque_keys.edx.keys import UsageKey
from edx_toggles.toggles.testutils import override_waffle_flag

from cms.djangoapps.contentstore import toggles
from cms.djangoapps.contentstore.tests.test_course_settings import CourseTestCase
from cms.djangoapps.contentstore.utils import reverse_course_url, reverse_usage_url
from openedx.core.lib.xblock_utils import get_course_update_items
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order


class CourseUpdateTest(CourseTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def create_update_url(self, provided_id=None, course_key=None):
        if course_key is None:
            course_key = self.course.id
        kwargs = {'provided_id': str(provided_id)} if provided_id else None
        return reverse_course_url('course_info_update_handler', course_key, kwargs=kwargs)

    # The do all and end all of unit test cases.
    @override_waffle_flag(toggles.LEGACY_STUDIO_UPDATES, True)
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

            return json.loads(resp.content.decode('utf-8'))

        resp = self.client.get_html(
            reverse_course_url('course_info_handler', self.course.id)
        )
        self.assertContains(resp, 'Course Updates', status_code=200)

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'  # lint-amnesty, pylint: disable=line-too-long
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

        self.assertHTMLEqual(content, json.loads(resp.content.decode('utf-8'))['content'],
                             "iframe w/ div")
        # refetch using provided id
        refetched = self.client.get_json(first_update_url)
        self.assertHTMLEqual(
            content, json.loads(refetched.content.decode('utf-8'))['content'], "get w/ provided id"
        )

        # now put in an evil update
        content = '<ol/>'
        payload = get_response(content, 'January 11, 2013')
        self.assertHTMLEqual(content, payload['content'], "self closing ol")

        course_update_url = self.create_update_url()
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(payload), 2)

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
        payload = json.loads(resp.content.decode('utf-8'))
        before_delete = len(payload)

        url = self.create_update_url(provided_id=this_id)
        resp = self.client.delete(url)
        payload = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(payload), before_delete - 1)

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
        update_date = "January 23, 2014"
        update_content = "Hello world!"
        update_data = "<ol><li><h2>" + update_date + "</h2>" + update_content + "</li></ol>"
        course_updates.data = update_data
        modulestore().update_item(course_updates, self.user.id)

        # test getting all updates list
        course_update_url = self.create_update_url()
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(payload, [{'date': update_date, 'content': update_content, 'id': 1}])
        self.assertEqual(len(payload), 1)

        # test getting single update item

        first_update_url = self.create_update_url(provided_id=payload[0]['id'])
        resp = self.client.get_json(first_update_url)
        payload = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(payload, {'date': 'January 23, 2014', 'content': 'Hello world!', 'id': 1})
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
        self.assertHTMLEqual(update_content, json.loads(resp.content.decode('utf-8'))['content'])
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items, [{'date': update_date, 'content': update_content, 'id': 1}])
        # course_updates 'data' field should not update automatically
        self.assertEqual(course_updates.data, '')

        # test delete course update item (soft delete)
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items, [{'date': update_date, 'content': update_content, 'id': 1}])
        # now try to delete first update item
        resp = self.client.delete(course_update_url + '1')
        self.assertEqual(json.loads(resp.content.decode('utf-8')), [])
        # confirm that course update is soft deleted ('status' flag set to 'deleted') in db
        course_updates = modulestore().get_item(location)
        self.assertEqual(course_updates.items,
                         [{'date': update_date, 'content': update_content, 'id': 1, 'status': 'deleted'}])

        # now try to get deleted update
        resp = self.client.get_json(course_update_url + '1')
        payload = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(payload.get('error'), "Course update not found.")
        self.assertEqual(resp.status_code, 404)

        # now check that course update don't munges html
        update_content = """&lt;problem>
                           &lt;p>&lt;/p>
                           &lt;multiplechoiceresponse>
                           <pre>&lt;problem>
                               &lt;p>&lt;/p></pre>
                           <div><foo>bar</foo></div>"""
        payload = {'content': update_content, 'date': update_date}
        resp = self.client.ajax_post(
            course_update_url, payload, REQUEST_METHOD="POST"
        )
        self.assertHTMLEqual(update_content, json.loads(resp.content.decode('utf-8'))['content'])

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

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'  # lint-amnesty, pylint: disable=line-too-long
        content = init_content + '</iframe>'
        payload = {'content': content, 'date': 'January 8, 2013'}

        course_update_url = self.create_update_url()
        resp = self.client.ajax_post(course_update_url, payload)

        payload = json.loads(resp.content.decode('utf-8'))

        self.assertHTMLEqual(payload['content'], content)

        # now confirm that the bad news and the iframe make up single update
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content.decode('utf-8'))
        self.assertEqual(len(payload), 1)

    def post_course_update(self):
        """
        Posts an update to the course
        """
        course_update_url = self.create_update_url(course_key=self.course.id)

        # create a course via the view handler
        self.client.ajax_post(course_update_url)

        content = "Sample update"
        payload = {'content': content, 'date': 'January 8, 2013'}
        resp = self.client.ajax_post(course_update_url, payload)

        # check that response status is 200 not 400
        self.assertEqual(resp.status_code, 200)

        payload = json.loads(resp.content.decode('utf-8'))
        self.assertHTMLEqual(payload['content'], content)

    def test_post_course_update(self):
        """
        Test that a user can successfully post on course updates and handouts of a course
        """
        self.post_course_update()

        updates_location = self.course.id.make_usage_key('course_info', 'updates')
        self.assertTrue(isinstance(updates_location, UsageKey))
        self.assertEqual(updates_location.block_id, 'updates')

        # check posting on handouts
        handouts_location = self.course.id.make_usage_key('course_info', 'handouts')
        course_handouts_url = reverse_usage_url('xblock_handler', handouts_location)

        content = "Sample handout"
        payload = {'data': content}
        resp = self.client.ajax_post(course_handouts_url, payload)

        # check that response status is 200 not 500
        self.assertEqual(resp.status_code, 200)

        payload = json.loads(resp.content.decode('utf-8'))
        self.assertHTMLEqual(payload['data'], content)

    def test_course_update_id(self):
        """
        Test that a user can successfully update a course update without a sequential ids
        """
        # create two course updates
        self.post_course_update()
        self.post_course_update()

        updates_location = self.course.id.make_usage_key('course_info', 'updates')
        self.assertTrue(isinstance(updates_location, UsageKey))
        self.assertEqual(updates_location.block_id, 'updates')

        course_updates = modulestore().get_item(updates_location)
        course_update_items = list(reversed(get_course_update_items(course_updates)))

        # Delete the course update with id 1
        course_update_items = [
            course_update_item for course_update_item in course_update_items if course_update_item.get('id') != 1
        ]

        course_updates.items = course_update_items
        course_updates.data = ""

        # update db record
        modulestore().update_item(course_updates, self.user.id)

        update_content = 'Testing'
        update_date = "January 23, 2014"
        course_update_url = self.create_update_url()
        payload = {'content': update_content, 'date': update_date}
        resp = self.client.ajax_post(
            course_update_url + '2', payload, HTTP_X_HTTP_METHOD_OVERRIDE="PUT", REQUEST_METHOD="POST"
        )

        self.assertHTMLEqual(update_content, json.loads(resp.content.decode('utf-8'))['content'])
        course_updates = modulestore().get_item(updates_location)
        del course_updates.items[0]["status"]
        self.assertEqual(course_updates.items, [{'date': update_date, 'content': update_content, 'id': 2}])
