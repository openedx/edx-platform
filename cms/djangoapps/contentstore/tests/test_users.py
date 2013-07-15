import json
from .utils import CourseTestCase
from django.core.urlresolvers import reverse


class UsersTestCase(CourseTestCase):
    def setUp(self):
        super(UsersTestCase, self).setUp()
        self.url = reverse("add_user", kwargs={"location": ""})

    def test_empty(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)
        content = json.loads(resp.content)
        self.assertEqual(content["Status"], "Failed")
