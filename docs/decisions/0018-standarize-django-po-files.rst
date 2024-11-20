Standardize ``django.po`` and ``djangojs.po`` files
===================================================

Status
------

Accepted

Context
-------

- The edx-platform splits its translations into ``mako-studio.po``,
  ``django-partial.po``, and 9 other files.  This was done with the
  intention of supporting more languages in the LMS than in
  the CMS (Studio).

- The edx-platform uses the ``i18n_tools segment`` to split the ``django.po``
  and ``djangojs.po`` files into smaller files. This is done with the goal of
  making it easier for translators to translate the files.

- When pulling from Transifex or cutting a new release, the translations are
  bundled into 2 files (``django.po`` and ``djangojs.po``).

- The `FC-0012 project <https://openedx.atlassian.net/l/cp/XGS0iCcQ>`_
  which implements `Translation Infrastructure update OEP-58`_
  is in progress. Upon completion, all translation files will live in
  the new `openedx-translations Transifex project`_.

- Consequently, repositories like ``edx-platform`` will pull translations via
  `openedx-atlas`_ command line tool as described in the `OEP-58`_ proposal.

- Several special steps would be needed to for the
  `extract-translation-source-files.yml`_ GitHub workflow in
  the `openedx-translations GitHub repository`_
  to extract the files from the ``edx-platform`` repo.
  This seems redundant and and it should be possible to simplify the process.

Decision: Only use two files for edx-platform translations (``django.po`` and ``djangojs.po``)
----------------------------------------------------------------------------------------------

edX Platform will push only two files (``django.po`` and
``djangojs.``) to the `openedx-translations Transifex project`_.

Consequences
------------

Pros:

- Translators will need to locate only two resources for the ``edx-platform``
  repo as opposed to 11 resources.
- Simplify the ``edx-platform`` translation extraction scripts in the
  `extract-translation-source-files.yml`_ GitHub workflow.
- The release cut process will be simplified as well by removing the
  translation merger step altogether.
- Translators will need one workflow for both latest (master) and named
  releases for the ``edx-platform`` repo.
- Simplifies the work of both the Build Test Release and Transifex working groups.

Cons:

- It will be harder for translators to focus on learner-facing text and de-prioritize
  educator-facing text.


Rejected Alternatives
---------------------

Combine into four files
^^^^^^^^^^^^^^^^^^^^^^^

This option tries to keep the original idea of splitting to allow translators
to focus on learner-facing text and de-prioritize educator-facing text.

The four files will be ``platform.po``, ``platform-js.po``, ``studio.po``
and ``studio-js.po``.

It will not concern the translators with the technical split
of the files into: ``wiki.po``, ``mako.po``, and ``django-partial.po``, etc.


In this option we'll create two new configuration files
``config.extract-oep58.yaml`` and ``config.pull-oep58.yaml`` to combine the
pofiles into the four files and then combine them into two files respectively:

.. code:: yaml

    # config.extract-oep58.yaml
    # This file is used by the ``make extract_translations`` when
    # the OPENEDX_COMBINE_FILES environment variable is enabled.
    generate_merge:
        platform.po:
            - django-partial.po
            - mako.po
            - wiki.po
            - edx_proctoring_proctortrack.po
        platform-js.po:
            - djangojs-partial.po
            - djangojs-account-settings-view.po
            - underscore.po
        studio.po:
            - django-studio.po
            - mako-studio.po
        studio-js.po:
            - djangojs-studio.po
            - underscore-studio.po

A corresponding ``Makefile`` change is needed:

.. code:: make

    extract_translations: ## extract localizable strings from sources
        i18n_tool extract -v
        if [ -z "$$OPENEDX_COMBINE_FILES" ]; then \
            i18n_tool generate --config=config.extract-oep58.yaml --verbose 1;
        fi

The other file would be ran after ``make pull_translations`` which will
be used to make the final ``django.po`` and ``djangojs.po`` files that are
usable by Django:

.. code:: yaml

    # config.pull-oep58.yaml
    # This file is used by the ``make pull_translations`` when
    # the OPENEDX_ATLAS_PULL environment variable is enabled.
    generate_merge:
        django.po:
            - platform.po
            - studio.po
        djangojs.po:
            - platform-js.po
            - studio-js.po


    pull_translations: ## extract localizable strings from sources
        if [ -z "$$OPENEDX_ATLAS_PULL" ]; then \
            atlas pull translations/edx-platform/conf/locale
            i18n_tool --config=config.pull-oep58.yaml generate --verbose 1;
        fi


This option involves multiple merge and split steps which adds complexity
for developers. Based on the `feedback in the decision pull request`_,
splitting the resources was a lesser used feature in the Open edX community.
Therefore, this option is rejected because the added complexity of this
option isn't justified.


.. _extract-translation-source-files.yml: https://github.com/openedx/openedx-translations/blob/2566e0c9a30d033e5dd8d05d4c12601c8e37b4ef/.github/workflows/extract-translation-source-files.yml
.. _openedx-translations GitHub repository: https://github.com/openedx/openedx-translations
.. _openedx-translations Transifex project: https://app.transifex.com/open-edx/openedx-translations/
.. _OEP-58: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _openedx-atlas: https://github.com/openedx/openedx-atlas/
.. _Translation Infrastructure update OEP-58: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _feedback in the decision pull request: https://github.com/openedx/edx-platform/pull/32994#issuecomment-1677390405
