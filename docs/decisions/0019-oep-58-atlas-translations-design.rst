Design for Refactoring Translations ``pull`` to use Atlas
##########################################################

Status
======

Pending

Context
=======

OEP-58 Translation Management overview
--------------------------------------

The `Translation Management update OEP-58`_ proposal has been merged with
the following changes to the way translations are managed in Open edX:

- Move Translation Files to the `openedx-translations repo`_
- Add `Transifex GitHub App <https://github.com/apps/transifex-integration>`_
  to openedx Organization
- Connect the `openedx-translations repo`_ to the
  `openedx-translations project`_
- Copy Transifex's Translation Memory and Combine Translators
- Get Translations Back for Deployment/Development and introduce the new
  `openedx-atlas`_ translation tool.

If you're new to the `Translation Management update OEP-58`_ proposal, please
review it in addition to the
`Approach Memo and Technical Discovery - Translations Infrastructure Implementation`_
document before continuing.

Current Architecture/Implementation for XBlocks and Plugins
-----------------------------------------------------------
As of now the Open edX XBlocks and Plugins are installed via ``pip`` with
their translations embedded within the Python package.

Bundling translations helps to ensure its always available. However, it also
means that in order to update translations, a full opensource contribution
process needs to happen. Somtimes the process takes a full month to
complete such as in the example below:

- `Added French (Canada) and Japanese - xblock-drag-and-drop-v2 #220`_


XBlockI18nService
-----------------

Once the translations are bundled and the XBlock/Plugin is installed the
XBlockI18nService will be able to find the Python translations and use load
them via the ``__init__`` method of the `XBlockI18nService`_ which finds
the ``text.mo`` files and make it available to the ``edx-platform``
during the execution of the XBlock.

The `XBlockI18nService implementation pull request`_ (2016) introduced the
support for XBlock translations in ``edx-platform`` and has the full
context of the implementation.

JavaScript Translations for XBocks
----------------------------------

As of September 2023, there is no centralized method to bundle JavaScript
translations in XBlocks. Non-XBlock plugins lacks JavaScript translations
support altogether.

The de-factor stadnard method for bundling JavaScript translations in XBlocks
is to use ``web_fragment`` and load the translations as part of the XBlock
frontend static files on every XBlock load.

The LTI Consumer XBlock embeds the translations in its ``web_fragment`` via
the `LtiConsumerXBlock._get_statici18n_js_url`_ and
`LtiConsumerXBlock.student_view`_ methods.

This design has it's trade-offs but it's been widely adopted and out of the
scope of this proposal. Therefore, we'll improve on the existing design to
load the ``atlas`` JavaScript translations instead of the bundled ones.

Decisions
=========

Proposed Design for edX Platform ``conf/locale`` translations
-------------------------------------------------------------

Update the ``make pull_translations`` command to use the ``atlas pull``
if the ``OPENEDX_ATLAS_PULL`` environment variable is set.

This has been the standard for all repositories as seen in both
`course-discovery atlas integration`_ and
`frontend-app-learning atlas integration`_.

The updated `edx-platform pull_translations`_ would look like the following::

  pull_translations:
    git clean -fdX conf/locale
    ifeq ($(OPENEDX_ATLAS_PULL),)
      find conf/locale -type d -mindepth 1 -maxdepth 1 -exec rm -rf {} +  # Remove stale translation files
      atlas pull $(ATLAS_PULL_ARGS) translations/edx-platform/conf/locale:conf/locale
    else
      i18n_tool transifex pull
    endif
    # The commands below are simplified for demonistration purposes
    i18n_tool generate --verbose 1
    i18n_tool validate --verbose
    paver i18n_compilejs


This mostly is a non-controversial change that has been done in other repos
already.

The next section is a little more intricate and requires more discussion.

Proposed Design for XBlocks and Plugins
---------------------------------------

The proposed design for XBlocks and Plugins is to use the ``atlas pull``
in a centrally managed way for all XBlocks and Plugins to circumvent the
the need for managing the translations in each XBlock.

The XBlock translations is already stored in the `openedx-translations repo`_
and is accessible by the `openedx-atlas`_ command-line.


New ``ENABLE_ATLAS_TRANSLATIONS`` Waffle Switch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``ENABLE_ATLAS_TRANSLATIONS`` switch will be disabled by default.
It will be used by the ``XBlockI18nService`` to determine which translations
to use for XBlocks until the `OEP-58`_ is fully implemented and
the non-atlas translations are removed.

The non-XBlock plugins such as `edx-val`_ are out of the scope of this
proposal and will be handled separately as stated in the :ref:`non-goals`
section.

New ``pull_plugins_translations`` command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Introduce new Django commands to the ``edx-platform``:

- ``manage.py lms pull_plugins_translations --list-only``: This command
  will list all the XBlocks and Plugins that are installed in the
  ``edx-platform`` virtual environment regardless of whether its run
  in Docker, devstack or Native Installation.

  If the command is executed with the ``--list-only`` flag it will print a
  list of Python *module names* (as opposed to git repository names) of the
  installed XBlocks and Plugins e.g.::

    $ manage.py lms atlas_pull_plugins_translations --list-only
    drag_and_drop_v2
    done
    eox_tenant

  This list doesn't include plugins that are bundled within the
  ``edx-platform`` repository itself such as the Video XBlock, the ``capa``
  module and others. The reason for this is that their translations are
  already included in the ``edx-platform`` translations.

- ``manage.py lms atlas_pull_plugins_translations``: This command
  will craft and executes the ``atlas pull`` command for the XBlocks and
  Plugins listed in the previous command. This command is will be added
  to the ``Makefile`` and can be executed for both development and production
  deployments.

  This command will run and ``atlas pull`` with the arguments below to pull
  the translations by module name::

    $ atlas pull \
        translations/edx-platform-links/drag_and_drop_v2:conf/plugins-locale/drag_and_drop_v2 \
        translations/edx-platform-links/done:conf/plugins-locale/done \
        translations/edx-platform-links/eox_tenant:conf/plugins-locale/eox_tenant

  **Note:** The command above is for demonstration purposes and may not work
  properly yet.

Changes to the `openedx-translations repo`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `openedx-translations repo`_ organizes the translations by the
GitHub repository name. However, once an XBlock is installed the repository
name is no longer known to the ``edx-platform``. Therefore, we provide two
ways to fetch the XBlock translations:

- By repo name: e.g. `translations/xblock-drag-and-drop-v2 directory`_.
- By module name: e.g.
  `translations/edx-platform-links/drag_and_drop_v2 directory`_.

This update is already implemented in the `openedx-translations repo`_ as of
`edx-platform-links PR #353`_ which includes the details of the changes.


BlockI18nService support for ``atlas`` Python translations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TBD:**

XBlockI18nService support for ``atlas`` JavaScript translations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**TBD:**

Dismissed Proposals
===================


XBlocks and plugins have their own "atlas pull" command
-------------------------------------------------------

This dismissed proposal intends to have each XBlock and Plugin have their
own ``make pull_translations`` and be responsible for managing pulling their
own translations from the `openedx-translations repo`_.

This proposal has been dismissed because it would require substantial work
to get into the details for the ``lib/python3.8/site-packages/`` directory
and ensure that the ``make pull_translations`` command won't corrupt the
virtual environment.

This is a non-trivial task and appears to add more complexity than necessary
for not much added benefit.


Goals
=====
#. Use ``atlas pull`` for the ``edx-platform`` repo.
#. Use ``atlas pull`` for the XBlocks and Plugins.
#. Allow Tutor and other advanced uses to craft their own ``atlas pull``
   commands by making the the plugins list available via Django commands.
#. Allow ``atlas pull`` to use the Python module names instead of the
   repository name of XBlocks and Plugins. This is already done in the
   `openedx-translations repo`_ via the
   ``extract-translation-source-files.yml``_ as described in the
   `edx-platform translations links`_ document.

.. _non-goals:

Non-Goals
=========

The following are non-goals for this proposal, although some are going to
be tackled in the future as part of the
`Translation Management update OEP-58`_ proposal.

#. Provide a fool-proof method for managing named-release translations.
   This will be a separate discussion.
#. Discuss the merge/segment strategy of the ``edx-platform``. This is being
   discussed in the
   `decision no. 0018 <https://github.com/openedx/edx-platform/pull/32994>`_.
#. Design a new XBlock frontend architecture. Instead this proposal works
   with the existing architecture.
#. Provide a new translation method for theme translations. This will be
   tackled later on.
#. Provide a new translation method for non-XBlock plugins such as
   ``edx-val``. This will be tackled later on as part of the `OEP-58`_
   proposal.

.. _Translation Management update OEP-58: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _OEP-58: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _openedx-atlas: https://github.com/openedx/openedx-atlas
.. _openedx-translations repo: https://github.com/openedx/openedx-translations
.. _extract-translation-source-files.yml: https://github.com/openedx/openedx-translations/blob/2566e0c9a30d033e5dd8d05d4c12601c8e37b4ef/.github/workflows/extract-translation-source-files.yml#L36-L43
.. _openedx-translations project: https://app.transifex.com/open-edx/openedx-translations/dashboard/

.. _Approach Memo and Technical Discovery - Translations Infrastructure Implementation: https://docs.google.com/document/d/11dFBCnbdHiCEdZp3pZeHdeH8m7Glla-XbIin7cnIOzU/edit
.. _Added French (Canada) and Japanese - xblock-drag-and-drop-v2 #220: https://github.com/openedx/xblock-drag-and-drop-v2/pull/220
.. _edx-platform translations links: https://github.com/openedx/openedx-translations/tree/main/translations/edx-platform-links
.. _XBlockI18nService: https://github.com/openedx/edx-platform/blob/6e28ba329e0a5354d7264ea834861bf0cae4ceb3/xmodule/modulestore/django.py#L359-L395
.. _XBlockI18nService implementation pull request: https://github.com/openedx/edx-platform/pull/11575/files#diff-0bbcc6c13d9bfc9d88fbe2fdf4fd97f6066a7a0f0bfffb82bc942378b7cf33e0R248

.. _course-discovery atlas integration: https://github.com/openedx/course-discovery/pull/4037
.. _frontend-app-learning atlas integration: https://github.com/openedx/frontend-app-learning/pull/1093
.. _edx-platform pull_translations: https://github.com/openedx/edx-platform/blob/0137881b8199701b2af7d07c9a01200e358e3d86/Makefile#L55-L64

.. _drag-and-drop-v2 xblock: https://github.com/openedx/xblock-drag-and-drop-v2/
.. _LTI Consumer XBlock: https://github.com/openedx/xblock-lti-consumer/
.. _edx-val: https://github.com/openedx/edx-val

.. _LtiConsumerXBlock._get_statici18n_js_url: https://github.com/openedx/xblock-lti-consumer/blob/7a142310a78ac393286c1e9e77c535ea520ab90b/lti_consumer/lti_xblock.py#L663-L677
.. _LtiConsumerXBlock.student_view: https://github.com/openedx/xblock-lti-consumer/blob/7a142310a78ac393286c1e9e77c535ea520ab90b/lti_consumer/lti_xblock.py#L1215C24-L1217


.. _edx-platform-links PR #353: https://github.com/openedx/openedx-translations/pull/353
.. _translations/xblock-drag-and-drop-v2 directory: https://github.com/openedx/openedx-translations/tree/8a01424fd8f42e9e76aed34e235c82ab654cdfc5/translations/xblock-drag-and-drop-v2
.. _translations/edx-platform-links/drag_and_drop_v2 directory: https://github.com/openedx/openedx-translations/blob/8a01424fd8f42e9e76aed34e235c82ab654cdfc5/translations/edx-platform-links/drag_and_drop_v2
