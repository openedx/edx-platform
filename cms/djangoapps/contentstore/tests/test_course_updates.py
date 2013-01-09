from cms.djangoapps.contentstore.tests.test_course_settings import CourseTestCase
from django.core.urlresolvers import reverse
import json
from cms.djangoapps.contentstore.course_info_model import update_course_updates


class CourseUpdateTest(CourseTestCase):
    def test_course_update(self):
        # first get the update to force the creation
        url = reverse('course_info', kwargs={'org' : self.course_location.org, 'course' : self.course_location.course, 
                                       'name' : self.course_location.name })
        self.client.get(url)

        content = '<iframe width="560" height="315" src="http://www.youtube.com/embed/RocY-Jd93XU" frameborder="0"></iframe>'
        payload = { 'content' : content,
                   'date' : 'January 8, 2013'}
        # No means to post w/ provided_id missing. django doesn't handle. So, go direct for the create
        payload = update_course_updates(['i4x', self.course_location.org, self.course_location.course, 'course_info', "updates"] , payload)
        
        url = reverse('course_info', kwargs={'org' : self.course_location.org, 'course' : self.course_location.course,
                                             'provided_id' : payload['id']})
         
        self.assertHTMLEqual(content, payload['content'], "single iframe")
        
        content += '<div>div <p>p</p></div>'
        payload['content'] = content
        resp = self.client.post(url, json.dumps(payload), "application/json")
        
        self.assertHTMLEqual(content, json.loads(resp.content)['content'], "iframe w/ div")
