Web (HTML) course certificates
==============================

Status
------
Accepted

Background
----------
edX-platform currently has code for both PDF and web (or HTML) course
certificates. Over time, much of the PDF certificate code has been deprecated
or disabled. In particular, edX-platform has not supported the generation of
PDF course certificates for some time.

Decision
--------
In the future, all code related to PDF certificates will be removed from
edx-platform. Only web certificates will be able to be generated or viewed.
First, the code to generate PDF certificates will be removed. Later, the code
to view existing PDF certificates will also be removed.

All course runs that use course certificates should be configured to use web
certificates.

Configuring web certificates
----------------------------
To configure web certificates, follow the documentation to `Enable Course
Certificates`_ and `Set Up Certificates in Studio`_.

In particular, the following things must be true in order for a web certificate
to be viewable:

* The *CERTIFICATES_HTML_VIEW* feature is globally enabled
* The course run has web certificates enabled
* The course run has at least 1 certificate created and activated

To enable the *CERTIFICATES_HTML_VIEW* feature, follow the instructions to
`Enable Course Certificates`_.

To ensure that a course run has web certificates enabled, follow the
instructions to `Set Up Certificates in Studio`_. In particular, follow the
steps to *Enable a Certificate*. This will result in the course run's course
overview having *cert_html_view_enabled* set to True

To ensure that a course run has at least 1 certificate created and activated,
follow the instructions to `Set Up Certificates in Studio`_. In particular,
follow the steps to *Create a Certificate* and to *Activate a Certificate*.
This will result in the course run's course overview having
*has_any_active_web_certificate* set to True

To find any course runs with downloadable certificates that might need to be
updated, you can run a query similar to this:

.. code-block:: SQL

    select distinct
        cert.course_id
    from
        CERTIFICATES_GENERATEDCERTIFICATE as cert
    join
        COURSE_OVERVIEWS_COURSEOVERVIEW as overview
    on
        cert.course_id = overview.id
    where
        cert.status = 'downloadable'
    and
    (
        overview.cert_html_view_enabled = False
    or
        overview.has_any_active_web_certificate = False
    )
    order by
        cert.course_id

Viewing a web certificate
-------------------------
To manually view a downloadable web certificate, first determine your site's
base URL. For edX, this is ``https://courses.edx.org/``

Next, find the desired certificate in the CERTIFICATES_GENERATEDCERTIFICATE
database table.

To view the certificate, find the *verify_uuid* from the table, then construct
a URL by appending */certificates/verify_uuid* to the base URL. For example,
the URL for edX will look like this:
``https://courses.edx.org/certificates/verify_uuid``

The web certificate will not be viewable if the course run is not
properly configured for web certificates. If this is the case, follow the
instructions above to configure the course run for web certificates.

Consequences
------------
To use course certificates, follow the documentation to `Enable Course
Certificates`_ and `Set Up Certificates in Studio`_.

All course runs that use course certificates should be configured to use web
certificates.

Once the code to generate and view PDF certificates is removed, only web
certificates will be able to be generated or viewed.

References
----------
Documentation for enabling course certificates:

* `Enable Course Certificates`_
* `Set Up Certificates in Studio`_

PRs that deprecated or disabled PDF certificates:

* `Disable PDF certificate generation`_
* `Deprecate web certificate setting`_

Related DEPR (edX deprecation process) tickets:

* `Remove PDF generation code`_
* `Remove PDF view code`_

.. _Enable Course Certificates: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/enable_certificates.html
.. _Deprecate web certificate setting: https://github.com/openedx/edx-platform/pull/17285
.. _Disable PDF certificate generation: https://github.com/openedx/edx-platform/pull/19833
.. _Set Up Certificates in Studio: https://edx.readthedocs.io/projects/open-edx-building-and-running-a-course/en/latest/set_up_course/studio_add_course_information/studio_creating_certificates.html
.. _Remove PDF generation code: https://openedx.atlassian.net/browse/DEPR-155
.. _Remove PDF view code: https://openedx.atlassian.net/browse/DEPR-157
