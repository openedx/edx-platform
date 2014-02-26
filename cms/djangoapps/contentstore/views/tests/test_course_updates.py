"""
unit tests for course_info views and models.
"""
import json

from contentstore.tests.test_course_settings import CourseTestCase
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.locator import BlockUsageLocator


class CourseUpdateTest(CourseTestCase):
    '''The do all and end all of unit test cases.'''
    def test_course_update(self):
        '''Go through each interface and ensure it works.'''
        def get_response(content, date):
            """
            Helper method for making call to server and returning response.

            Does not supply a provided_id.
            """
            payload = {'content': content, 'date': date}
            url = update_locator.url_reverse('course_info_update/')

            resp = self.client.ajax_post(url, payload)
            self.assertContains(resp, '', status_code=200)

            return json.loads(resp.content)

        course_locator = loc_mapper().translate_location(
            self.course.location.course_id, self.course.location, False, True
        )
        resp = self.client.get_html(course_locator.url_reverse('course_info/'))
        self.assertContains(resp, 'Course Updates', status_code=200)
        update_locator = loc_mapper().translate_location(
            self.course.location.course_id, self.course.location.replace(category='course_info', name='updates'),
            False, True
        )

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'
        content = init_content + '</iframe>'
        payload = get_response(content, 'January 8, 2013')
        self.assertHTMLEqual(payload['content'], content)

        first_update_url = update_locator.url_reverse('course_info_update', str(payload['id']))
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

        course_update_url = update_locator.url_reverse('course_info_update/')
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
            self.client.ajax_post(course_update_url + '/9', payload),
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
        self.assertContains(self.client.delete(course_update_url + '/19'), "delete", status_code=400)

        # now delete a real update
        content = 'blah blah'
        payload = get_response(content, 'January 28, 2013')
        this_id = payload['id']
        self.assertHTMLEqual(content, payload['content'], "single iframe")
        # first count the entries
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        before_delete = len(payload)

        url = update_locator.url_reverse('course_info_update/', str(this_id))
        resp = self.client.delete(url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == before_delete - 1)

    def test_course_updates_compatibility(self):
        '''
        Test that course updates doesn't break on old data (content in 'data' field).
        Note: new data will save as list in 'items' field.
        '''
        # get the updates and populate 'data' field with some data.
        location = self.course.location.replace(category='course_info', name='updates')
        modulestore('direct').create_and_save_xmodule(location)
        course_updates = modulestore('direct').get_item(location)
        update_date = u"January 23, 2014"
        update_content = u"Hello world!"
        update_data = u"<ol><li><h2>" + update_date + "</h2>" + update_content + "</li></ol>"
        course_updates.data = update_data
        modulestore('direct').update_item(course_updates, self.user)

        update_locator = loc_mapper().translate_location(
            self.course.location.course_id, location, False, True
        )
        # test getting all updates list
        course_update_url = update_locator.url_reverse('course_info_update/')
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        self.assertEqual(payload, [{u'date': update_date, u'content': update_content, u'id': 1}])
        self.assertTrue(len(payload) == 1)

        # test getting single update item
        first_update_url = update_locator.url_reverse('course_info_update', str(payload[0]['id']))
        resp = self.client.get_json(first_update_url)
        payload = json.loads(resp.content)
        self.assertEqual(payload, {u'date': u'January 23, 2014', u'content': u'Hello world!', u'id': 1})
        self.assertHTMLEqual(update_date, payload['date'])
        self.assertHTMLEqual(update_content, payload['content'])

        # test that while updating it converts old data (with string format in 'data' field)
        # to new data (with list format in 'items' field) and respectively updates 'data' field.
        course_updates = modulestore('direct').get_item(location)
        self.assertEqual(course_updates.items, [])
        # now try to update first update item
        update_content = 'Testing'
        payload = {'content': update_content, 'date': update_date}
        resp = self.client.ajax_post(
            course_update_url + '/1', payload, HTTP_X_HTTP_METHOD_OVERRIDE="PUT", REQUEST_METHOD="POST"
        )
        self.assertHTMLEqual(update_content, json.loads(resp.content)['content'])
        course_updates = modulestore('direct').get_item(location)
        self.assertEqual(course_updates.items, [{u'date': update_date, u'content': update_content, u'id': 1}])
        # course_updates 'data' field should update accordingly
        update_data = u"<section><article><h2>{date}</h2>{content}</article></section>".format(date=update_date, content=update_content)
        self.assertEqual(course_updates.data, update_data)

        # test delete course update item (soft delete)
        course_updates = modulestore('direct').get_item(location)
        self.assertEqual(course_updates.items, [{u'date': update_date, u'content': update_content, u'id': 1}])
        # now try to delete first update item
        resp = self.client.delete(course_update_url + '/1')
        self.assertEqual(json.loads(resp.content), [])
        # confirm that course update is soft deleted ('status' flag set to 'deleted') in db
        course_updates = modulestore('direct').get_item(location)
        self.assertEqual(course_updates.items,
                         [{u'date': update_date, u'content': update_content, u'id': 1, u'status': 'deleted'}])

        # now try to get deleted update
        resp = self.client.get_json(course_update_url + '/1')
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
        location = self.course.location.replace(category='course_info', name='updates')
        modulestore('direct').create_and_save_xmodule(location)
        course_updates = modulestore('direct').get_item(location)
        course_updates.data = 'bad news'
        modulestore('direct').update_item(course_updates, self.user.id)

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'
        content = init_content + '</iframe>'
        payload = {'content': content, 'date': 'January 8, 2013'}

        update_locator = loc_mapper().translate_location(
            self.course.location.course_id, location, False, True
        )
        course_update_url = update_locator.url_reverse('course_info_update/')
        resp = self.client.ajax_post(course_update_url, payload)

        payload = json.loads(resp.content)

        self.assertHTMLEqual(payload['content'], content)

        # now confirm that the bad news and the iframe make up single update
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == 1)

    def test_post_course_update(self):
        """
        Test that a user can successfully post on course updates of a course whose location in not in loc_mapper
        """
        # create a course via the view handler
        course_location = Location(['i4x', 'Org_1', 'Course_1', 'course', 'Run_1'])
        course_locator = loc_mapper().translate_location(
            course_location.course_id, course_location, False, True
        )
        self.client.ajax_post(
            course_locator.url_reverse('course'),
            {
                'org': course_location.org,
                'number': course_location.course,
                'display_name': 'test course',
                'run': course_location.name,
            }
        )

        branch = u'draft'
        version = None
        block = u'updates'
        updates_locator = BlockUsageLocator(
            package_id=course_location.course_id.replace('/', '.'), branch=branch, version_guid=version, block_id=block
        )

        content = u"Sample update"
        payload = {'content': content, 'date': 'January 8, 2013'}
        course_update_url = updates_locator.url_reverse('course_info_update')
        resp = self.client.ajax_post(course_update_url, payload)

        # check that response status is 200 not 400
        self.assertEqual(resp.status_code, 200)

        payload = json.loads(resp.content)
        self.assertHTMLEqual(payload['content'], content)

        # now test that calling translate_location returns a locator whose block_id is 'updates'
        updates_location = course_location.replace(category='course_info', name=block)
        updates_locator = loc_mapper().translate_location(course_location.course_id, updates_location)
        self.assertTrue(isinstance(updates_locator, BlockUsageLocator))
        self.assertEqual(updates_locator.block_id, block)
