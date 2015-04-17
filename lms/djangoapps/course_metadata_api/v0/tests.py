"""
Run these tests @ Devstack:
    paver test_system -s lms --fasttest --verbose --test_id=lms/djangoapps/course_structure_api
"""


class CourseListTests(CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_metadata_api:v0:list'

    def test_get(self):
        """
        The view should return a list of all courses.
        """
        response = self.http_get(reverse(self.view))
        self.assertEqual(response.status_code, 200)
        data = response.data
        courses = data['results']

        self.assertEqual(len(courses), 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['num_pages'], 1)

        self.assertValidResponseCourse(courses[0], self.empty_course)
        self.assertValidResponseCourse(courses[1], self.course)


class CourseDetailTests(CourseDetailMixin, CourseViewTestsMixin, ModuleStoreTestCase):
    view = 'course_metadata_api:v0:detail'

    def test_get(self):
        response = super(CourseDetailTests, self).test_get()
        self.assertValidResponseCourse(response.data, self.course)
