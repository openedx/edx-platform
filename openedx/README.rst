Open edX
--------

This is the root package for Open edX. The intent is that all importable code
from Open edX will eventually live here, including the code in the lms, cms,
and common directories.

If you're adding a new Django app, place it in core/djangoapps. If you're adding
utilities that require Django, place them in core/djangolib.  If you're adding
code that defines no Django models or views of its own but is widely useful, put it
in core/lib.

Note: All new code should be created in this package, and the legacy code will
be moved here gradually. For now the code is not structured like this, and hence
legacy code will continue to live in a number of different packages.
