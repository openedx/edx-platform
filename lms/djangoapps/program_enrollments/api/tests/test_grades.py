"""
(Future home of) Tests for program_enrollments grade-reading Python API.

Currently, we do not directly unit test `load_program_course_grades`.
This is okay for now because it is used in
`rest_api.v1.views` and is thus tested through `rest_api.v1.tests.test_views`.
Eventually it would be good to directly test the Python API function and just use
mocks in the view tests.
This file serves as a placeholder and reminder to do that the next time there
is development on the program_enrollments grades API.
"""
