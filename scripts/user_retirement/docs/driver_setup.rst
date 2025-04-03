.. _driver-setup:

Setting Up the User Retirement Driver Scripts
#############################################

`scripts/user_retirement <https://github.com/openedx/edx-platform/tree/master/scripts/user_retirement>`_
is a directory of Python scripts designed to plug into various automation
tooling. It also contains readme file having details of how to run the scripts.
Included in this directory are two scripts intended to drive the user
retirement workflow.

``get_learners_to_retire.py``
    Generates a list of users that are ready for immediate retirement.  Users
    are "ready" after a certain number of days spent in the ``PENDING`` state,
    specified by the ``--cool_off_days`` argument. Produces an output intended
    for consumption by Jenkins in order to spawn separate downstream builds for
    each user.
``retire_one_learner.py``
    Retires the user specified by the ``--username`` argument.

These two scripts share a required ``--config_file`` argument, which specifies
the driver configuration file for your environment (for example, production).
This configuration file is a YAML file that contains LMS auth secrets, API URLs,
and retirement pipeline stages specific to that environment. Here is an example
of a driver configuration file.

.. code-block:: yaml

   client_id: <client ID for the retirement service user>
   client_secret: <client secret for the retirement service user>

   base_urls:
       lms: https://courses.example.com/
       ecommerce: https://ecommerce.example.com/
       credentials: https://credentials.example.com/

   retirement_pipeline:
       - ['RETIRING_EMAIL_LISTS', 'EMAIL_LISTS_COMPLETE', 'LMS', 'retirement_retire_mailings']
       - ['RETIRING_ENROLLMENTS', 'ENROLLMENTS_COMPLETE', 'LMS', 'retirement_unenroll']
       - ['RETIRING_LMS_MISC', 'LMS_MISC_COMPLETE', 'LMS', 'retirement_lms_retire_misc']
       - ['RETIRING_LMS', 'LMS_COMPLETE', 'LMS', 'retirement_lms_retire']

The ``client_id`` and ``client_secret`` keys contain the oauth credentials.
These credentials are simply copied from the output of the
``create_dot_application`` management command described in
:ref:`retirement-service-user`.

The ``base_urls`` section in the configuration file defines the mappings of
IDA to base URLs used by the scripts to construct API URLs.  Only the LMS is
mandatory here, but if any of your pipeline states contain API calls to other
services, those services must also be present in the ``base_urls`` section.

The ``retirement_pipeline`` section defines the steps, state names, and order
of execution for each environment. Each item is a list in the form of:

#. Start state name
#. End state name
#. IDA to call against (LMS, ECOMMERCE, or CREDENTIALS currently)
#. Method name to call in
   `edx_api.py <https://github.com/openedx/edx-platform/blob/master/scripts/user_retirement/utils/edx_api.py>`_

For example: ``['RETIRING_CREDENTIALS', 'CREDENTIALS_COMPLETE', 'CREDENTIALS',
'retire_learner']`` will set the user's state to ``RETIRING_CREDENTIALS``, call
a pre-instantiated ``retire_learner`` method in the ``CredentialsApi``, then set
the user's state to ``CREDENTIALS_COMPLETE``.

Examples
********

The following are some examples of how to use the driver scripts.

Set Up Environment
==================

Follow this `readme <https://github.com/openedx/edx-platform/tree/master/scripts/user_retirement#readme>`_ to set up your execution environment.

List of Targeted Learners
=========================

Generate a list of learners that are ready for retirement (those learners who
have selected and confirmed account deletion and have been in the ``PENDING``
state for the time specified ``cool_off_days``).

.. code-block:: bash

   mkdir learners_to_retire
   get_learners_to_retire.py \
       --config_file=path/to/config.yml \
       --output_dir=learners_to_retire \
       --cool_off_days=5

Run Retirement Script
=====================

After running these commands, the ``learners_to_retire`` directory  contains
several INI files, each containing a single line in the form of ``USERNAME
=<username-of-learner>``. Iterate over these files while executing the
``retire_one_learner.py`` script on each learner with a command like the following.

.. code-block:: bash

   retire_one_learner.py \
       --config_file=path/to/config.yml \
       --username=<username-of-learner-to-retire>


Using the Driver Scripts in an Automated Framework
**************************************************

At edX, we call the user retirement scripts from
`Jenkins <https://jenkins.io/>`_ jobs on one of our internal Jenkins
services. The user retirement driver scripts are intended to be agnostic
about which automation framework you use, but they were only fully tested
from Jenkins.

For more information about how we execute these scripts at edX, see the
following wiki articles:

* `User Retirement Jenkins Implementation <https://openedx.atlassian.net/wiki/spaces/PLAT/pages/704872737/User+Retirement+Jenkins+Implementation>`_
* `How to: retirement Jenkins jobs development and testing <https://openedx.atlassian.net/wiki/spaces/PLAT/pages/698221444/How+to+retirement+Jenkins+jobs+development+and+testing>`_

And check out the Groovy DSL files we use to seed these jobs:

* `platform/jobs/RetirementJobs.groovy in edx/jenkins-job-dsl <https://github.com/edx/jenkins-job-dsl/blob/master/platform/jobs/RetirementJobs.groovy>`_
* `platform/jobs/RetirementJobEdxTriggers.groovy in edx/jenkins-job-dsl <https://github.com/edx/jenkins-job-dsl/blob/master/platform/jobs/RetirementJobEdxTriggers.groovy>`_

.. include:: ../../../../links/links.rst
