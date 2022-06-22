edx-platform workflows
######################

Each YAML files here defines an automated `GitHub Actions`_ *workflow*. Workflows are triggered by specific events, such as pushes to branches/PRs, releases, or manual triggering. Each workflow, which is defined by a YAML file in this directory, specifies how to respond to its triggers by defining one or more *jobs*. Each job is made of up of several *steps*. Both jobs and steps can be defined in-place, or they can ``use:`` other actions/workflows defined in this repo or externally.

.. _GitHub Actions: https://docs.github.com/en/actions

Guidelines for adding new workflows
***********************************

Shared workflows
================

If similar or identical workflows are needed across multiple repositories, then add a generic version of the workflow to the central `.github repository`_, which can be referenced by wrapper workflows in other repositories. For example, `commitlint is implemented once`_ in .github and then `used by other repositories`_ for their individual CI suites.


Workflow & job naming
=====================

Give workflows informative but short names (using the top-level ``name:`` key). Keeping the workflow name down to one or two words.

Give jobs informative but short names using lowercase letters, numbers, and hyphens. By default, a job's name is displayed as the YAML key you used to define it within the ``jobs:`` dictionary. Unless you are doing something complicated with a build matrix, there is no need to set the ``name:`` key for each job.

Follow these guidelines will make it easier for pull request authors to read the names of the many checks we run using GitHub Actions:

.. image:: https://user-images.githubusercontent.com/3628148/175115478-13685047-9d6a-41a7-86b1-14432b90a8b8.png
   :alt: Many different checks running on a pull request
   :width: 600

CI Checks
=========

Implement continuous integration (CI) checks as jobs, and group related jobs into workflows. For example, the `Quality workflow`_ defines jobs for pylinting, type checking, and other miscellanous code quality verifications; the `upstream Tests workflow`_ defines jobs for running unit tests on various shards; and so on.

Prefix the YAML file name for CI workflows with ``ci-`` (for example, ``ci-migrations.yml``).

If you expect that a CI check should pass for every PR, make it a Required Check from `GitHub branch settings`_. If you don't have access to do so, reach out to a repository maintainer.

.. image:: https://user-images.githubusercontent.com/3628148/175115316-bdede68f-edee-4729-b581-2d858269aadb.png
   :alt: A different view of checks running on a pull request, showcasing how related jobs are grouped into workflows

.. _.github repository: https://github.com/openedx/.github
.. _commitlint is implemented once: https://github.com/openedx/.github/blob/master/.github/workflows/commitlint.yml
.. _used by other repositories: https://github.com/openedx/edx-platform/blob/master/.github/workflows/ci-commitlint.yml
.. _Quality workflow: https://github.com/openedx/edx-platform/blob/master/.github/workflows/ci-quality.yml
.. _upstream Tests workflow: https://github.com/openedx/edx-platform/blob/master/.github/workflows/ci-tests.yml
.. _GitHub branch settings: https://github.com/openedx/edx-platform/settings/branches

