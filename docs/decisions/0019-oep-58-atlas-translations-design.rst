Design for Refactoring Translations ``pull`` to use Atlas
##########################################################

Status
======

Accepted

Context
=======

OEP-58 Translation Management overview
--------------------------------------

The `Translation Management update OEP-58`_ proposal has been merged with
the following changes to the way translations are managed in the Open edX platform:

- Move Translation Files to the `openedx-translations repo`_
- Add the `Transifex GitHub App <https://github.com/apps/transifex-integration>`_
  to openedx Organization
- Connect the `openedx-translations repo`_ to the
  `openedx-translations Transifex project`_
- Copy `Transifex Translation Memory`_ into from the both of the
  `edx-platform Transifex project`_ and the `xblocks Transifex project`_ into
  the new `openedx-translations Transifex project`_
- Utilize `openedx-atlas`_ to pull translations for development/deployment.

If you're new to the `OEP-58`_ proposal, please
review the `OEP-58 Specifications`_ in addition to the
Key Metrics and Expected Results section in the
`Approach Memo and Technical Discovery - Translations Infrastructure Implementation`_
document before continuing.

Pre-OEP-58 Architecture/Implementation for XBlocks and Plugins
--------------------------------------------------------------

Before `OEP-58`_, Open edX XBlocks and Open edX plugins had the following:

- Translations live in the GitHub repository.
- Translations are packaged with the rest of the code when published to pypi

Pros:

- Translations are always available after installation.

Cons:

- This can mean a complex integration with Transifex
- This can mean a lengthy manual PR review process up to a month such as in
  the following example:
  `Added French (Canada) and Japanese - xblock-drag-and-drop-v2 #220`_

XBlockI18nService
-----------------

The `XBlockI18nService`_ loads translations for installed XBlocks via its
``__init__`` method. XBlock translations are only used during the
during the execution of the XBlock.

The `XBlockI18nService implementation pull request`_ (2016) introduced
support for XBlock translations in ``edx-platform`` and has the full
context of the implementation.

.. _js-translations:

JavaScript Translations for XBocks
----------------------------------

As of September 2023, there is no centralized method to bundle JavaScript
translations in XBlocks. Non-XBlock plugins lack JavaScript translation
support altogether.

The de-facto standard method for bundling JavaScript translations in XBlocks
is to use ``web_fragment`` and load the translations as part of the XBlock
frontend static files on every XBlock load.

The LTI Consumer XBlock embeds the translations in its ``web_fragment`` via
the `LtiConsumerXBlock._get_statici18n_js_url`_ and
`LtiConsumerXBlock.student_view`_ methods.

In order to separate the XBlock translations from the platform, it's isolated
in a separate ``gettext`` namespace. For example, the Drag and Drop XBlock
namespace is ``DragAndDropI18N`` which is hardcoded in multiple places such
as:

- `XBlock Makefile compile_translations rule`_
- `XBlock compiled JavaScript text.js translations`_
- `XBlock main JavaScript file`_

`OEP-58`_ does not change this structure, it just makes the necessary changes
to pull translations from the `openedx-translations repo`_ via ``atlas``
instead of having them live in the XBlock repository itself.

Decisions
=========

Proposed Design for edX Platform ``conf/locale`` translations
-------------------------------------------------------------

We're going to use ``atlas`` in ``make pull_translations`` like we do in
`course-discovery atlas integration`_ and
`frontend-app-learning atlas integration`_.

Proposed Design for XBlocks and Plugins
---------------------------------------

Instead of storing translation files for each XBlock and Plugin in their
respective repositories,
we will use `openedx-atlas`_ to pull them from the
`openedx-translations repo`_.


New ``atlas_pull_plugin_translations`` command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Introduce new Django commands to the ``edx-platform``:

- ``manage.py lms atlas_pull_plugin_translations --list``: List all XBlocks and
  Plugins installed in the ``edx-platform`` virtual environment. This will
  list the Python *module names* (as opposed to git repository names) of the
  installed XBlocks and Plugins e.g.::

    $ manage.py lms atlas_pull_plugin_translations --list
    drag_and_drop_v2
    done
    eox_tenant

  This list doesn't include plugins that are bundled within the
  ``edx-platform`` repository itself. Translations for bundled plugins
  are included in the ``edx-platform`` translation files.

- ``manage.py lms atlas_pull_plugin_translations``: This command
  will pull translations for installed XBlocks and Plugins by module name::

    $ atlas pull --expand-glob \
        'translations/*/drag_and_drop_v2/conf/locale:conf/plugins-locale/drag_and_drop_v2' \
        'translations/*/done/conf/locale:conf/plugins-locale/done' \
        'translations/*/edx_proctoring/conf/locale:conf/plugins-locale/edx_proctoring'

  Resulting in the following file tree::

    $ tree conf/plugins-locale/
    conf/plugins-locale/
    ├── done
    │   ├── ar
    │   │   └── LC_MESSAGES
    │   │       └── django.po
    │   ├── de
    │   │   └── LC_MESSAGES
    │   │       └── django.po
    │   ├── en
    │   │   └── LC_MESSAGES
    │   │       └── django.po
    │   └── fr_CA
    │       └── LC_MESSAGES
    │           └── django.po
    ├── drag_and_drop_v2
    │   ├── ar
    │   │   └── LC_MESSAGES
    │   │       └── django.po
    │   ├── en
    │   │   └── LC_MESSAGES
    │   │       └── django.po
    │   └── fr_CA
    │       └── LC_MESSAGES
    │           └── django.po
    └── edx_proctoring
        ├── ar
        │   └── LC_MESSAGES
        │       └── djangojs.po
        ├── de
        │   └── LC_MESSAGES
        │       └── djangojs.po
        ├── en
        │   └── LC_MESSAGES
        │       ├── djangojs.po
        │       └── django.po
        └── fr_CA
            └── LC_MESSAGES
                ├── djangojs.po
                └── django.po


BlockI18nService support for ``atlas`` Python translations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``get_python_locale_directory`` will support two modes:

#. If translations for the XBlock/plugin has been pulled by ``atlas``
   from the `openedx-translations repo`_, it will be used. For example, if the
   ``edx-platform/conf/plugins-locale/drag_and_drop_v2/ar/LC_MESSAGES/django.po``
   path exists, it will be used for the Drag and Drop XBlock.

#. Otherwise, the bundled translation files in the XBlock packages will be
   used. The fallback path for the Drag and Drop XBlock will be
   ``lib/python3.8/site-packages/drag_and_drop_v2/translations/ar/LC_MESSAGES/text.po``.

This fallback is used to maintain backwards compatibility with existing
XBlocks that may or may not be included in the `openedx-translations repo`_.
Third-party XBlocks that are not included in the
`xblocks Transifex project`_, such as the `Lime Survey XBlock`_,
will benefit from this backwards compatibility.

New ``compile_plugin_js_translations`` command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An ``XBlock.i18n_js_namespace`` property will be added for
the ``compile_plugin_js_translations`` to generate JavaScript translations
in a centrally managed manner for installed XBlocks.

A ``compile_plugin_js_translations`` command will loop over XBlock
modules that has the ``i18n_js_namespace``
property set and compile the JavaScript translations via the `compilejsi18n`_
command.

For example if the Drag and Drop XBlock has
``i18n_js_namespace = 'DragAndDropI18N'``, the
``compile_plugin_js_translations`` command will execute the following
commands::

  i18n_tool generate -v  # Generate the .mo files
  python manage.py compilejsi18n --namespace DragAndDropI18N --output conf/plugins-locale/drag_and_drop_v2/js/


XBlockI18nService support for ``atlas`` JavaScript translations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``get_javascript_locale_path`` method will be added to the
``XBlockI18nService`` to provide XBlocks the
appropriate path to ``django.js`` translation files. This method
will allow XBlocks to utilize legacy packaged translations
or ``atlas``.

A ``i18n_js_namespace`` property will be added
to generate JavaScript translations in a centrally managed manner for all
XBlocks as described in the :ref:`js-translations` section.

For example, the `Drag and Drop XBlock get_static_i18n_js_url`_ will need to
be updated to support the new ``XBlockI18nService``
``get_javascript_locale_path`` method and the namespace.

.. code:: diff

     class DragAndDropBlock(XBlock):

   +   i18n_js_namespace = 'DragAndDropI18N'

       @staticmethod
       def _get_statici18n_js_url():
           """
           Returns the Javascript translation file for the currently selected language, if any found by
           `pkg_resources`
           """
           lang_code = translation.get_language()
           if not lang_code:
               return None

   +       # TODO: Make this the default once OEP-58 is implemented.
   +       if hasattr(self.i18n_service, 'get_javascript_locale_path'):
   +           atlas_locale_path = self.i18n_service.get_javascript_locale_path()
   +           if atlas_locale_path:
   +               return atlas_locale_path

           text_js = 'public/js/translations/{lang_code}/text.js'
           country_code = lang_code.split('-')[0]
           for code in (translation.to_locale(lang_code), lang_code, country_code):
               if pkg_resources.resource_exists(loader.module_name, text_js.format(lang_code=code)):
                   return text_js.format(lang_code=code)
           return None


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
due to the fact that XBlocks and plugins won't be used outside the
context of ``edx-platform``.


Goals
=====
#. Use ``atlas pull`` for the ``edx-platform`` repo.
#. Use ``atlas pull`` for the XBlocks and Plugins.
#. Allow Tutor and other advanced uses to craft their own ``atlas pull``
   commands by making the the plugins list available via Django commands.
#. Allow ``atlas pull`` to use the Python module names instead of the
   repository name of XBlocks and Plugins which is supported via the
   `atlas pull --expand-glob`_ option.

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

.. _OEP-58 Specifications: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _Translation Management update OEP-58: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _OEP-58: https://open-edx-proposals.readthedocs.io/en/latest/architectural-decisions/oep-0058-arch-translations-management.html#specification
.. _openedx-atlas: https://github.com/openedx/openedx-atlas
.. _openedx-translations repo: https://github.com/openedx/openedx-translations
.. _extract-translation-source-files.yml: https://github.com/openedx/openedx-translations/blob/2566e0c9a30d033e5dd8d05d4c12601c8e37b4ef/.github/workflows/extract-translation-source-files.yml#L36-L43
.. _openedx-translations Transifex project: https://app.transifex.com/open-edx/openedx-translations/dashboard/

.. _Approach Memo and Technical Discovery - Translations Infrastructure Implementation: https://docs.google.com/document/d/11dFBCnbdHiCEdZp3pZeHdeH8m7Glla-XbIin7cnIOzU/edit
.. _Added French (Canada) and Japanese - xblock-drag-and-drop-v2 #220: https://github.com/openedx/xblock-drag-and-drop-v2/pull/220
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
.. _Drag and Drop XBlock get_static_i18n_js_url: https://github.com/openedx/xblock-drag-and-drop-v2/blob/66e8d3517fe8c0db55c1a3907ff253c2a4562a7e/drag_and_drop_v2/drag_and_drop_v2.py#L318-L332

.. _XBlock compiled JavaScript text.js translations: https://github.com/openedx/xblock-drag-and-drop-v2/blob/b8ab1ecd9168ab1dba21f994ee4bfedb6a57d11f/drag_and_drop_v2/public/js/translations/tr/text.js#L3
.. _XBlock Makefile compile_translations rule: https://github.com/openedx/xblock-drag-and-drop-v2/blob/66e8d3517fe8c0db55c1a3907ff253c2a4562a7e/Makefile#L41
.. _XBlock main JavaScript file: https://github.com/openedx/xblock-drag-and-drop-v2/blob/b8ab1ecd9168ab1dba21f994ee4bfedb6a57d11f/drag_and_drop_v2/public/js/drag_and_drop.js#L6


.. _translations/xblock-drag-and-drop-v2 directory: https://github.com/openedx/openedx-translations/tree/8a01424fd8f42e9e76aed34e235c82ab654cdfc5/translations/xblock-drag-and-drop-v2
.. _atlas pull --expand-glob: https://github.com/openedx/openedx-atlas/blob/main/docs/decisions/0001-support-glob-pattern.rst

.. _compilejsi18n: https://django-statici18n.readthedocs.io/en/latest/commands.html#compilejsi18n
.. _Transifex Translation Memory: https://help.transifex.com/en/articles/6224636-introduction-to-translation-memory
.. _edx-platform Transifex project: https://www.transifex.com/open-edx/edx-platform/
.. _xblocks Transifex project: https://www.transifex.com/open-edx/xblocks/

.. _Lime Survey XBlock: https://github.com/eduNEXT/xblock-limesurvey
