==============================================
How to test View Auth for course-related views
==============================================

What to test
------------
Each view endpoint that exposes an internal API endpoint - like in files in the rest_api folder - must
be tested for the following.

- Only authenticated users can access the endpoint.
- Only users with the correct permissions (authorization) can access the endpoint.
- All data and params that are part of the request are properly validated.

How to test
-----------
The `AuthorizeStaffTestCase` class provides a set of tests that can be used to test the authorization
of a view. If you inherit from this class, these tests will be automatically run. For details,
please look at the source code of the `AuthorizeStaffTestCase` class.

A lot of these tests can be easily implemented by inheriting from the `AuthorizeStaffTestCase`.
This parent class assumes that the view is for a specific course and that only users who have access
to the course can access the view. (They are either staff or instructors for the course, or global admin).

Here is an example of how to test a view that requires a user to be authenticated and have access to a course.

.. code-block:: python

    from cms.djangoapps.contentstore.tests.test_utils import AuthorizeStaffTestCase
    from django.test import TestCase
    from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
    from django.urls import reverse

    class TestMyGetView(AuthorizeStaffTestCase, ModuleStoreTestCase, TestCase):
        def make_request(self, course_id=None, data=None):
            url = self.get_url(self.course.id)
            response = self.client.get(url, data)
            return response

        def get_url(self, course_key):
            url = reverse(
                'cms.djangoapps.contentstore:v0:my_get_view',
                kwargs={'course_id': self.course.id}
            )
            return url

As you can see, you need to inherit from `AuthorizeStaffTestCase` and `ModuleStoreTestCase`, and then either
`TestCase` or `APITestCase` depending on the type of view you are testing. For cookie-based
authentication, `TestCase` is sufficient, for Oauth2 use `ApiTestCase`.

The only two methods you need to implement are `make_request` and `get_url`. The `make_request` method
should make the request to the view and return the response. The `get_url` method should return the URL
for the view you are testing.

Overwriting Tests
-----------------
If you need different behavior you can overwrite the tests from the parent class.
For example, if students should have access to the view, simply implement the
`test_student` method in your test class.

Adding other tests
------------------
If you want to test other things in the view - let's say validation -
it's easy to just add another `test_...` function to your test class
and you can use the `make_request` method to make the request.
