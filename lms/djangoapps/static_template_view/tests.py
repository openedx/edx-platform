from django.test import TestCase
from django.test.client import Client


class SimpleTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_render(self):
        """
        Render a normal page, like jobs
        """
        response = self.client.get("/jobs")
        self.assertEquals(response.status_code, 200)


    def test_render_press_release(self):
        """
        Render press releases from generic URL match
        """
        # since I had to remap files, pedantically test all press releases
        # published to date. Decent positive test while we're at it.
        all_releases = [
            "/press/mit-and-harvard-announce-edx",
            "/press/uc-berkeley-joins-edx",
            "/press/edX-announces-proctored-exam-testing",
            "/press/elsevier-collaborates-with-edx",
            "/press/ut-joins-edx",
            "/press/cengage-to-provide-book-content",
            "/press/gates-foundation-announcement",
            "/press/wellesley-college-joins-edx",
            "/press/georgetown-joins-edx",
            "/press/spring-courses",
            "/press/lewin-course-announcement",
            "/press/bostonx-announcement",
            "/press/eric-lander-secret-of-life",
            "/press/edx-expands-internationally",
            "/press/xblock_announcement",
            "/press/stanford-to-work-with-edx",
        ]

        for rel in all_releases:
            response = self.client.get(rel)
            self.assertNotContains(response, "PAGE NOT FOUND", status_code=200)

        # should work with caps
        response = self.client.get("/press/STANFORD-to-work-with-edx")
        self.assertContains(response, "Stanford", status_code=200)

        # negative test
        response = self.client.get("/press/this-shouldnt-work")
        self.assertEqual(response.status_code, 404)

        # can someone do something fishy?  no.
        response = self.client.get("/press/../homework.html")
        self.assertEqual(response.status_code, 404)

        # "." in is ascii 2E
        response = self.client.get("/press/%2E%2E/homework.html")
        self.assertEqual(response.status_code, 404)

