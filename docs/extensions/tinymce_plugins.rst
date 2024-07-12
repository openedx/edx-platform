TinyMCE (Visual Text/HTML Editor) Plugins
-----------------------------------------

The flexibility of the TinyMCE Visual Text and HTML editor makes it possible to configure and extend the editor using different plugins. In order to make use of that modularity in Studio, you'll need to follow two different steps.

Installing Plugins
==================

Initially, we'll need to specify which plugins need to install so that they can be bundled with the static assets.

There's a decent `guide on installing the plugins through the edX configuration`_, specifically using the ``TINYMCE_ADDITIONAL_PLUGINS_LIST`` configuration variable.

Enabling Plugins
================

Enabling the plugins requires adding a Studio environment setting which the JavaScript code can access, ``JS_ENV_EXTRA_CONFIG``. It is simply a dictionary which would contain different extra JavaScript configurations.

The extra JavaScript configuration that's responsible for enabling TinyMCE plugins is ``TINYMCE_ADDITIONAL_PLUGINS``. This is a list of different TinyMCE plugins which you would want to enable.

Each TinyMCE plugin has the following attributes.

.. list-table::
   :header-rows: 1
   :widths: 15 10 75

   * - attribute
     - type
     - description
   * - ``name``
     - string
     - The name of the TinyMCE plugin which would be included in the editor's list of plugins.
   * - ``toolbar``
     - boolean
     - Indicates whether this plugin should be displayed in the toolbar or not.
   * - ``extra_settings``
     - object
     - Specifies the extra plugin settings that need to be added to the TinyMCE editor's configuration.

Here's an example:

.. code:: yaml

   EDXAPP_CMS_ENV_EXTRA:
     JS_ENV_EXTRA_CONFIG:
       TINYMCE_ADDITIONAL_PLUGINS:
       - name: adsklink
         toolbar: true
         extra_settings:
           linktypes:
           - Download
           - Offer
           filetypes:
           - PDF
           - ZIP
           - Video
           - Design
           orientations:
           - Vertical
           - Horizontal
           styles:
           - Primary
           - Normal
           - Secondary

.. _guide on installing the plugins through the edX configuration: https://github.com/openedx/configuration/blob/master/playbooks/roles/tinymce_plugins/README.rst
