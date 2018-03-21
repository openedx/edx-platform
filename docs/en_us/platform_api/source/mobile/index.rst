.. _edX Platform Mobile API Version 0.5:

#####################################
Mobile API Version 0.5 (Deprecated)
#####################################

The mobile API version 0.5 is deprecated. EdX platform developers should not
implement new client functions that use the mobile API version 0.5.

You can get information about the courses offered by an edX platform
installation by using the ``/api/courses/v1/courses/`` REST endpoint.

You can get information about the parameters and return values of
``/api/courses/v1/courses`` from the Django REST framework web page for that
endpoint. For example, `https://courses.edx.org/api/courses/v1/courses/`_
provides information about the courses offered by edx.org.

.. note::

    The documentation available at `docs.edx.org`_ does not include information
    about the ``/api/courses/v1/courses/`` REST endpoint. Developer
    documentation for the ``/api/courses/v1/courses/`` is planned in upcoming
    documentation releases.

You can get and update information about learners by using the edX platform
user API. For more information about getting and updating learner information
in the user API, see :ref:`Get and Update the User's Account Information`.

.. include:: ../links.rst
