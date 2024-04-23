edx-sandbox: a Python environment for sandboxed execution with CodeJail
#######################################################################

The requirements in this directory describe a Python environment separate from
the general edx-platform environment. When correctly configured with
`CodeJail <https://github.com/openedx/codejail>`_, edx-platform can use
it to execute untrusted code, particularly instructor-authored Python code
within ``<script type="loncapa/python">`` ProblemBlock tags.

Files in this directory
***********************

base.in
=======

This is the current set of requirements or the edx-sandbox
environment, and it is used to generate the ``.txt`` files described below.
These requirements share some constraints with the general edx-platform
requirements (via ``../constraints.txt``), but otherwise, they are completely
separate.

We do not recommend installing from this file directly, because
the packages are not pinned.

base.txt
========

These are the latest requirement pins for edx-sandbox.
They are regularly updated with the latest compatible versions of each package.

Install from this file if you wish to always run the latest edx-sandbox
environment. Take note that there will periodically be breaking changes to
``base.txt``. For example, we may update the Python version used to generate
the pins, which may break edx-sandbox environments running older Python
versions.

releases/(RELEASE_NAME).txt
===========================

*e.g. releases/redwood.txt, releases/sumac.txt, etc.*

Starting with Quince, every named Open edX release adds one of these files.
They contain the requirement pins corresponding to ``base.txt`` at the time
of each release.

Install from one of these files if you want to run a stable edx-sandbox
environment without breaking changes.

Support windows
***************

Only ``base.txt`` and the latest ``release/*.txt`` from the latest named
release are supported by the Open edX community. However, we will leave
old ``release/*.txt`` files in the repository to assist:

* operators who want to stagger their edx-sandbox upgrade from their general
  edx-platform upgrade
* operators who need to temporarily roll back their edx-sandbox environments
  so that instructors can fix their loncapa Python code.
