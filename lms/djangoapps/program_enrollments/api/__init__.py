"""
Python API exposed by the program_enrollments app to other in-process apps.

The functions are split into separate files for code organization, but they
are imported into here so they can be imported directly from
`lms.djangoapps.program_enrollments.api`.

When adding new functions to this API, add them to the appropriate module
within the /api/ folder, and then "expose" them here by importing them.

We use explicit imports here because (1) it hides internal variables in the
sub-modules and (2) it provides a nice catalog of functions for someone
using this API.
"""
