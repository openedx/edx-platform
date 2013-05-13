'''unit tests for course_info views and models.'''
from contentstore.tests.test_course_settings import CourseTestCase
from django.core.urlresolvers import reverse
import json


class CourseUpdateTest(CourseTestCase):
    '''The do all and end all of unit test cases.'''
    def test_course_update(self):
        '''Go through each interface and ensure it works.'''
        # first get the update to force the creation
        url = reverse('course_info',
                      kwargs={'org': self.course_location.org,
                      'course': self.course_location.course,
                      'name': self.course_location.name})
        self.client.get(url)

        init_content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0">'
        content = init_content + '</iframe>'
        payload = {'content': content,
                   'date': 'January 8, 2013'}
        url = reverse('course_info_json',
                      kwargs={'org': self.course_location.org,
                              'course': self.course_location.course,
                              'provided_id': ''})

        resp = self.client.post(url, json.dumps(payload), "application/json")

        payload = json.loads(resp.content)

        self.assertHTMLEqual(payload['content'], content)

        first_update_url = reverse('course_info_json',
                                   kwargs={'org': self.course_location.org,
                                           'course': self.course_location.course,
                                           'provided_id': payload['id']})
        content += '<div>div <p>p<br/></p></div>'
        payload['content'] = content
        resp = self.client.post(first_update_url, json.dumps(payload),
                                "application/json")

        self.assertHTMLEqual(content, json.loads(resp.content)['content'],
                             "iframe w/ div")

        # now put in an evil update
        content = '<ol/>'
        payload = {'content': content,
                   'date': 'January 11, 2013'}
        url = reverse('course_info_json',
                      kwargs={'org': self.course_location.org,
                              'course': self.course_location.course,
                              'provided_id': ''})

        resp = self.client.post(url, json.dumps(payload), "application/json")

        payload = json.loads(resp.content)

        self.assertHTMLEqual(content, payload['content'], "self closing ol")

        url = reverse('course_info_json',
                      kwargs={'org': self.course_location.org,
                              'course': self.course_location.course,
                              'provided_id': ''})
        resp = self.client.get(url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == 2)

        # can't test non-json paylod b/c expect_json throws error
        # try json w/o required fields
        self.assertContains(self.client.post(url, json.dumps({'garbage': 1}),
                                             "application/json"),
                            'Failed to save', status_code=400)

        # now try to update a non-existent update
        url = reverse('course_info_json',
                      kwargs={'org': self.course_location.org,
                              'course': self.course_location.course,
                              'provided_id': '9'})
        content = 'blah blah'
        payload = {'content': content,
                   'date': 'January 21, 2013'}
        self.assertContains(
            self.client.post(url, json.dumps(payload), "application/json"),
            'Failed to save', status_code=400)

        # update w/ malformed html
        content = '<garbage tag No closing brace to force <span>error</span>'
        payload = {'content': content,
                   'date': 'January 11, 2013'}
        url = reverse('course_info_json', kwargs={'org': self.course_location.org,
                                                  'course': self.course_location.course,
                                                  'provided_id': ''})

        self.assertContains(
            self.client.post(url, json.dumps(payload), "application/json"),
            '<garbage')

        # set to valid html which would break an xml parser
        content = "<p><br><br></p>"
        payload = {'content': content,
                   'date': 'January 11, 2013'}
        url = reverse('course_info_json', kwargs={'org': self.course_location.org,
                                                  'course': self.course_location.course,
                                                  'provided_id': ''})

        resp = self.client.post(url, json.dumps(payload), "application/json")
        payload = json.loads(resp.content)
        self.assertHTMLEqual(content, json.loads(resp.content)['content'])

        # now try to delete a non-existent update
        url = reverse('course_info_json', kwargs={'org': self.course_location.org,
                                                  'course': self.course_location.course,
                                                  'provided_id': '19'})
        payload = {'content': content,
                   'date': 'January 21, 2013'}
        self.assertContains(self.client.delete(url), "delete", status_code=400)

        # now delete a real update
        content = 'blah blah'
        payload = {'content': content,
                   'date': 'January 28, 2013'}
        url = reverse('course_info_json', kwargs={'org': self.course_location.org,
                                                  'course': self.course_location.course,
                                                  'provided_id': ''})
        resp = self.client.post(url, json.dumps(payload), "application/json")
        payload = json.loads(resp.content)
        this_id = payload['id']
        self.assertHTMLEqual(content, payload['content'], "single iframe")
        # first count the entries
        url = reverse('course_info_json',
                      kwargs={'org': self.course_location.org,
                              'course': self.course_location.course,
                              'provided_id': ''})
        resp = self.client.get(url)
        payload = json.loads(resp.content)
        before_delete = len(payload)

        url = reverse('course_info_json',
                      kwargs={'org': self.course_location.org,
                              'course': self.course_location.course,
                              'provided_id': this_id})
        resp = self.client.delete(url)
        payload = json.loads(resp.content)
        self.assertTrue(len(payload) == before_delete - 1)
