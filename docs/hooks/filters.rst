Open edX Filters
================

How to use
----------

Using openedx-filters in your code is very straight forward. We can consider the
two possible cases:

Configuring a filter
^^^^^^^^^^^^^^^^^^^^

Implement pipeline steps
************************

Let's say you want to consult student's information with a third party service
before generating the students certificate. This is a common use case for filters,
where the functions part of the filter's pipeline will perform the consulting tasks and
decide the execution flow for the application. These functions are the pipeline steps,
and can be implemented in an installable Python library:

.. code-block:: python

    # Step implementation taken from openedx-filters-samples plugin
    from openedx_filters import PipelineStep
    from openedx_filters.learning.filters import CertificateCreationRequested

    class StopCertificateCreation(PipelineStep):

        def run_filter(self, user, course_id, mode, status):
            # Consult third party service and check if continue
            # ...
            # User not in third party service, denied certificate generation
            raise CertificateCreationRequested.PreventCertificateCreation(
                "You can't generate a certificate from this site."
            )

There's two key components to the implementation:

1. The filter step must be a subclass of ``PipelineStep``.

2. The ``run_filter`` signature must match the filters definition, eg.,
the previous step matches the method's definition in CertificateCreationRequested.

Attach/hook pipeline to filter
******************************

After implementing the pipeline steps, we have to tell the certificate creation
filter to execute our pipeline.

.. code-block:: python

    OPEN_EDX_FILTERS_CONFIG = {
        "org.openedx.learning.certificate.creation.requested.v1": {
            "fail_silently": False,
            "pipeline": [
                "openedx_filters_samples.samples.pipeline.StopCertificateCreation"
            ]
        },
    }

Triggering a filter
^^^^^^^^^^^^^^^^^^^

In order to execute a filter in your own plugin/library, you must install the
plugin where the steps are implemented and also, ``openedx-filters``.

.. code-block:: python

    # Code taken from lms/djangoapps/certificates/generation_handler.py
    from openedx_filters.learning.filters import CertificateCreationRequested

    try:
        self.user, self.course_id, self.mode, self.status = CertificateCreationRequested.run_filter(
            user=self.user, course_id=self.course_id, mode=self.mode, status=self.status,
        )
    except CertificateCreationRequested.PreventCertificateCreation as exc:
        raise CertificateGenerationNotAllowed(str(exc)) from exc

Testing filters' steps
^^^^^^^^^^^^^^^^^^^^^^

It's pretty straightforward to test your pipeline steps, you'll need to include the
``openedx-filters`` library in your testing dependencies and configure them in your test case.

.. code-block:: python

   from openedx_filters.learning.filters import CertificateCreationRequested

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.certificate.creation.requested.v1": {
                "fail_silently": False,
                "pipeline": [
                    "openedx_filters_samples.samples.pipeline.StopCertificateCreation"
                ]
            }
        }
    )
    def test_certificate_creation_requested_filter(self):
        """
        Test filter triggered before the certificate creation process starts.

        Expected results:
          - The pipeline step configured for the filter raises PreventCertificateCreation
          when the conditions are met.
        """
        with self.assertRaises(CertificateCreationRequested.PreventCertificateCreation):
            CertificateCreationRequested.run_filter(
                user=self.user, course_key=self.course_key, mode="audit",
            )

        # run your assertions

Changes in the ``openedx-filters`` library that are not compatible with your code
should break this kind of test in CI and let you know you need to upgrade your code.
The main limitation while testing filters' steps it's their arguments, as they are edxapp
memory objects, but that can be solved in CI using Python mocks.

Live example
^^^^^^^^^^^^

For filter steps samples you can visit the `openedx-filters-samples`_ plugin, where
you can find minimal steps exemplifying the different ways on how to use
``openedx-filters``.

.. _openedx-filters-samples: https://github.com/eduNEXT/openedx-filters-samples


Index of Filters
-----------------

This list contains the filters currently being executed by edx-platform. The provided
links target both the definition of the filter in the openedx-filters library as
well as the trigger location in this same repository.


.. list-table::
   :widths: 35 50 20

   * - *Name*
     - *Type*
     - *Date added*

   * - `StudentRegistrationRequested <https://github.com/eduNEXT/openedx-filters/blob/main/openedx_filters/learning/filters.py#L9>`_
     - org.openedx.learning.student.registration.requested.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/register.py#L261>`_

   * - `StudentLoginRequested <https://github.com/eduNEXT/openedx-filters/blob/main/openedx_filters/learning/filters.py#L40>`_
     - org.openedx.learning.student.login.requested.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/user_authn/views/login.py#L569>`_

   * - `CourseEnrollmentStarted <https://github.com/eduNEXT/openedx-filters/blob/main/openedx_filters/learning/filters.py#L70>`_
     - org.openedx.learning.course.enrollment.started.v1
     - `2022-06-14 <https://github.com/openedx/edx-platform/blob/master/common/djangoapps/student/models.py#L1675>`_

   * - `CourseUnenrollmentStarted <https://github.com/eduNEXT/openedx-filters/blob/main/openedx_filters/learning/filters.py#L98>`_
     - org.openedx.learning.course.unenrollment.started.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/common/djangoapps/student/models.py#L1752>`_

   * - `CertificateCreationRequested <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L142>`_
     - org.openedx.learning.certificate.creation.requested.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/lms/djangoapps/certificates/generation_handler.py#L119>`_

   * - `CertificateRenderStarted <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L161>`_
     - org.openedx.learning.certificate.render.started.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/lms/djangoapps/certificates/views/webview.py#L649>`_

   * - `CohortChangeRequested <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L230>`_
     - org.openedx.learning.cohort.change.requested.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/openedx/core/djangoapps/course_groups/models.py#L138>`_

   * - `CohortAssignmentRequested <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L256>`_
     - org.openedx.learning.cohort.assignment.requested.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/openedx/core/djangoapps/course_groups/models.py#L149>`_

   * - `CourseAboutRenderStarted <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L281>`_
     - org.openedx.learning.course_about.render.started.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/lms/djangoapps/courseware/views/views.py#L1015>`_

   * - `DashboardRenderStarted <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L354>`_
     - org.openedx.learning.dashboard.render.started.v1
     - `2022-06-14 <https://github.com/eduNEXT/edx-platform/blob/master/common/djangoapps/student/views/dashboard.py#L878>`_

   * - `VerticalBlockChildRenderStarted <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L427>`_
     - org.openedx.learning.veritical_block_child.render.started.v1
     - `2022-08-18 <https://github.com/openedx/edx-platform/blob/master/xmodule/vertical_block.py#L170>`_

   * - `VerticalBlockRenderCompleted <https://github.com/openedx/openedx-filters/blob/main/openedx_filters/learning/filters.py#L476>`_
     - org.openedx.learning.veritical_block.render.completed.v1
     - `2022-02-18 <https://github.com/openedx/edx-platform/blob/master/xmodule/vertical_block.py#L121>`_
