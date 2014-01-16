'''unit tests for course_info views and models.'''
from contentstore.tests.test_course_settings import CourseTestCase
import json
from xmodule.modulestore.django import modulestore, loc_mapper


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

    def test_no_ol_course_update(self):
        '''Test trying to add to a saved course_update which is not an ol.'''
        # get the updates and set to something wrong
        location = self.course.location.replace(category='course_info', name='updates')
        modulestore('direct').create_and_save_xmodule(location)
        course_updates = modulestore('direct').get_item(location)
        course_updates.data = 'bad news'
        modulestore('direct').update_item(course_updates, 'test_course_updates')

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

        # now confirm that the bad news and the iframe make up 2 updates
        resp = self.client.get_json(course_update_url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == 2)
