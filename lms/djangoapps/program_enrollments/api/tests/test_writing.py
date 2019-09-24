"""
(Future home of) Tests for program enrollment writing Python API.

Currently, we do not directly unit test the functions in api/writing.py.
This is okay for now because they are all used in
`rest_api.v1.views` and is thus tested through `rest_api.v1.tests.test_views`.
Eventually it would be good to directly test the Python API function and just use
mocks in the view tests.
This file serves as a placeholder and reminder to do that the next time there
is development on the program_enrollments writing API.
"""
from __future__ import absolute_import, unicode_literals
