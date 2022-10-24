#################
Open edX Platform
#################
| |License: AGPL v3| |Status| |Python CI|

.. |License: AGPL v3| image:: https://img.shields.io/badge/License-AGPL_v3-blue.svg
  :target: https://www.gnu.org/licenses/agpl-3.0

.. |Python CI| image:: https://github.com/openedx/edx-platform/actions/workflows/unit-tests.yml/badge.svg
  :target: https://github.com/openedx/edx-platform/actions/workflows/unit-tests.yml

.. |Status| image:: https://img.shields.io/badge/status-maintained-31c653

Purpose
-------
The `Open edX Platform <https://openedx.org>`_ is a service-oriented platform for authoring and
delivering online learning at any scale.  The platform is written in
Python and JavaScript and makes extensive use of the Django
framework. At the highest level, the platform is composed of a
monolith, some independently deployable applications (IDAs), and
micro-frontends (MFEs) based on the ReactJS.

This repository hosts the monolith at the center of the Open edX
platform.  Functionally, the edx-platform repository provides two services:

* CMS (Content Management Service), which powers Open edX Studio, the platform's learning content authoring environment; and
* LMS (Learning Management Service), which delivers learning content.

Installation
------------

Installing and running an Open edX instance is not simple.  We strongly
recommend that you use a service provider to run the software for you.  They
have free trials that make it easy to get started:
https://openedx.org/get-started/

If you will be modifying edx-platform code, the `Open edX Developer Stack`_ (Devstack) is
a Docker-based development environment.

If you want to run your own Open edX server and have the technical skills to do
so, `Open edX Installation Options`_ explains your options.

.. _Open edX Developer Stack: https://github.com/openedx/devstack
.. _Open edX Installation Options:  https://openedx.atlassian.net/wiki/spaces/OpenOPS/pages/60227779/Open+edX+Installation+Options

License
-------

The code in this repository is licensed under version 3 of the AGPL
unless otherwise noted. Please see the `LICENSE`_ file for details.

.. _LICENSE: https://github.com/openedx/edx-platform/blob/master/LICENSE


More about Open edX
-------------------

See the `Open edX site`_ to learn more about the Open edX world. You can find
information about hosting, extending, and contributing to Open edX software. In
addition, the Open edX site provides product announcements, the Open edX blog,
and other rich community resources.

.. _Open edX site: https://openedx.org

Documentation
-------------

Documentation can be found at https://docs.edx.org.


Getting Help
------------

If you're having trouble, we have discussion forums at
https://discuss.openedx.org where you can connect with others in the community.

Our real-time conversations are on Slack. You can request a `Slack
invitation`_, then join our `community Slack team`_.

For more information about these options, see the `Getting Help`_ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack team: http://openedx.slack.com/
.. _Getting Help: https://openedx.org/getting-help


Issue Tracker
-------------

We use JIRA for our issue tracker, not GitHub issues. You can search
`previously reported issues`_.  If you need to report a problem,
please make a free account on our JIRA and `create a new issue`_.

.. _previously reported issues: https://openedx.atlassian.net/projects/CRI/issues
.. _create a new issue: https://openedx.atlassian.net/secure/CreateIssue.jspa?issuetype=1&pid=11900


How to Contribute
-----------------

Contributions are welcome! The first step is to submit a signed
`individual contributor agreement`_.  See our `CONTRIBUTING`_ file for more
information – it also contains guidelines for how to maintain high code
quality, which will make your contribution more likely to be accepted.


Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email
security@edx.org.

.. _individual contributor agreement: https://openedx.org/cla
.. _CONTRIBUTING: https://github.com/openedx/edx-platform/blob/master/CONTRIBUTING.rst
