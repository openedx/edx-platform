edx-platform workflows
######################

Each YAML files here defines an automated `GitHub Actions`_ *workflow*. Workflows are triggered by specific events, such as pushes to branches/PRs, releases, or manual triggering. Each workflow, which is defined by a YAML file in this directory, specifies how to respond to its triggers by defining one or more *jobs*. Each job is made of up of several *steps*. Both jobs and steps can be defined in-place, or they can ``use:`` other actions/workflows defined in this repo or externally.

.. _GitHub Actions: https://docs.github.com/en/actions

Guidelines for adding new workflows
***********************************

* If the similar or identical workflows are needed across multiple repositories, then add a generic version of the workflow to the central `.github repository`_, which can be referenced by wrapper workflows in other repositories. For example, `commitlint is implemented once`_ in .github and then `used by other repositories`_ for their individual CI suites.
* Give workflows informative but short names (using the top-level ``name:`` key). Keeping the workflow name down to one or two words makes it easier to see workflow and job details.
* Give jobs informative but short names using lowercase letters, numbers, and hyphens. By default, a job's name is displayed as the YAML key you used to define it within the ``jobs:`` dictionary. Unless you are doing something complicated with a build matrix, there is no need to set the ``name:`` key for each job.
* Implement continuous integration (CI) checks as jobs, and group related jobs into workflows. For example, the `Quality workflow`_ defines jobs for pylinting, type checking, and other miscellanous code quality verifications; the `upstream Tests workflow`_ defines jobs for running unit tests on various shards; and so on.


.. _.github repository: https://github.com/openedx/.github
.. _commitlint is implemented once: https://github.com/openedx/.github/blob/master/.github/workflows/commitlint.yml
.. _used by other repositories: https://github.com/openedx/edx-platform/blob/master/.github/workflows/ci-commitlint.yml
.. _Quality workflow: https://github.com/openedx/edx-platform/blob/master/.github/workflows/ci-quality.yml
.. _upstream Tests workflow: https://github.com/openedx/edx-platform/blob/master/.github/workflows/ci-quality.yml

