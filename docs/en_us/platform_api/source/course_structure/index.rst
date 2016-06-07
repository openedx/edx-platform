.. _EdX Platform Course Structure API Version 0:

#############################################
Course Structure API Version 0 (Deprecated)
#############################################

The course structure API version 0 is deprecated. EdX platform developers
should not implement new client functions that use the course structure API
version 0.

You can get information about the courses offered by an edX platform
installation by using the ``/api/courses/v1/courses/`` REST endpoint.

You can get information about the parameters and return values of
``/api/courses/v1/courses`` from the Django REST framework web page for that
endpoint. For example, `https://courses.edx.org/api/courses/v1/courses/`_ provides information about the courses offered by edx.org.

.. note::

    The documentation available at `docs.edx.org`_ does not include information
    about the ``/api/courses/v1/courses/`` REST endpoint. Developer
    documentation for the ``/api/courses/v1/courses/`` is planned in upcoming
    documentation releases.

.. include:: ../links.rst
