#####################
Comprehensive Theming
#####################


Comprehensive Theming lets you customize the appearance of your Open edX
installation.  You can override Sass and CSS settings, images, or entire HTML
templates.

Eventually, Comprehensive Theming will obsolete existing theming mechanisms,
but for now they co-exist peacefully. This document describes how to use
Comprehensive Theming, and also the changes you'll need to make to keep other
theming mechanisms working.


Creating a theme
================

A theme is a directory of assets.  You can create this directory wherever you
like, it does not have to be inside the edx-platform directory.  The structure
within this directory mirrors the assets in the edx-platform repo itself.
Files you provide in your theme are used in place of the same-named files in
edx-platform.  Here's a sample::

    my-theme
    └── lms
        ├── static
        │   ├── images
        │   │   └── logo.png
        │   └── sass
        │       ├── _overrides.scss
        │       ├── lms-main-rtl.scss
        │       └── lms-main.scss
        └── templates
            ├── footer.html
            └── header.html

The top directory is named whatever you like.  This example uses "my-theme".
The files provided here override the files in edx-platform.  In this case, the
``my-theme/lms/static/sass/lms-main.scss`` file is used in place of the
``edx-platform/lms/static/sass/lms-main.scss`` file.


Images
------

Images can be substituted simply by placing the new image at the right place
in the theme directory.  In our example above, the lms/static/images/logo.png
image is overridden.


Sass/CSS
--------

Most CSS styling in Open edX is done with Sass files compiled to CSS. EdX is
converting over to use `Bootstrap Theming`_, so you can follow the instructions
defined here:

.. _Bootstrap Theming: https://getbootstrap.com/docs/4.0/getting-started/theming/

There are two example themes provided within edx-platform's themes directory:

* red-theme: switches Open edX's primary color to red instead of blue
* dark-theme: uses a dark background and light foreground colors

For more details, see `Changing Themes for an Open edX Site`_.

.. _Changing Themes for an Open edX Site: https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/changing_appearance/theming/index.html

HTML Templates
--------------

You can make changes to HTML templates by copying them to your theme directory
in the appropriate place, and making the changes you need.  Keep in mind that
in the future if you upgrade the Open edX code, you may have to update the
copied template in your theme also.

Template Names
==============

Here are the list of template names that you *should* use in your comprehensive
theme (so far):

* ``header.html``
* ``footer.html``

Installing your theme
---------------------

To use your theme, you need to add a configuration value pointing to your theme
directory. There are two ways to do this.

#.  If you usually edit server-vars.yml:

    #.  As the vagrant user, edit (or create)
        /edx/app/edx_ansible/server-vars.yml to add the
        ``edxapp_comprehensive_theme_dir`` value::

            edxapp_comprehensive_theme_dir: '/full/path/to/my-theme'

    #.  Run the update script::

            $ sudo /edx/bin/update configuration master
            $ sudo /edx/bin/update edx-platform HEAD

#.  Otherwise, edit the /edx/app/edxapp/lms.yml file to add the
    ``COMPREHENSIVE_THEME_DIRS`` value::

        "COMPREHENSIVE_THEME_DIRS": ["/full/path/to/my-theme"],

Restart your site.  Your changes should now be visible.


Comprehensive Theming
=====================
* The ``PROFILE_IMAGE_DEFAULT_FILENAME`` Django setting is now ignored.


"Stanford" theming
==================

If you want to continue using the "Stanford" theming system, there are a few
changes you'll need to make.

Create the following new files in the ``sass`` directory of your theme:

* lms-main.scss
* lms-main-rtl.scss
* lms-course.scss
* lms-course-rtl.scss
* lms-footer.scss
* lms-footer-rtl.scss

The contents of each of these files will be very similar. Here's what
``lms-main.scss`` should look like::

    $static-path: '../../../..';
    @import 'lms/static/sass/lms-main';
    @import '_default';

Each file should set the ``$static-path`` variable to a relative path that
points to the ``lms/static`` directory inside of ``edx-platform``. Then,
it should ``@import`` the sass file under ``lms/static/sass`` that matches
its name: ``lms-footer.scss`` should import ``lms/static/sass/lms-footer``,
for example. Finally, the file should import the ``_default`` name, which
refers to the ``_default.scss`` Sass file that should already exist in your
Stanford theme directory.

If your theme uses a different name than "default", you'll need to use that
name in the ``@import`` line.

Run the ``update_assets`` command to recompile the theme::

    $ paver update_assets lms --settings=production

Microsites
==========

If you want to continue using the "Microsites" theming system, there are a few
changes you'll need to make. A few templates have been renamed, or folded into
other templates:

* ``header_extra.html`` has been renamed to ``head-extra.html``. This file
  was always inserted into the ``<head>`` element of the page, rather than
  the header of the ``<body>`` element, so this change makes the name more
  accurate.

* ``google_analytics.html`` has been removed. The contents of this template
  can and should be added to the ``head-extra.html`` template.

* ``google_tag_manager.html`` has been renamed to ``body-initial.html``.

In addition, there are some other changes you'll need to make:

* The ``google_analytics_file`` config value is now ignored. If your Open edX
  installation has a Google Analytics account ID set, the Google Analytics
  JavaScript will be included automatically on your site using that account ID.
  You can set this account ID either using the "GOOGLE_ANALYTICS_ACCOUNT" value
  in the Django settings, or by setting the newly-added "GOOGLE_ANALYTICS_ACCOUNT"
  config value in your site configuration.

* You can set the google site verification ID in the GOOGLE_SITE_VERIFICATION_ID
  in your site configuration. Otherwise, edit the /edx/app/edxapp/lms.yml
  file to set the value for GOOGLE_SITE_VERIFICATION_ID. Setting the value for
  GOOGLE_SITE_VERIFICATION_ID will add the meta tag for google site verification
  in the lms/templates/main.html which is the main Mako template that all page
  templates should include.

* If you don't want the Google Analytics JavaScript to be output at all in your
  site, set the "GOOGLE_ANALYTICS_ACCOUNT" config value to the empty string.
  If you want to customize the way that Google Analytics is loaded, set the
  "GOOGLE_ANALYTICS_ACCOUNT" config value to the empty string, and then load
  Google Analytics yourself (with whatever customizations you want) in your
  ``head-extra.html`` template.

* The ``css_overrides_file`` config value is now ignored. To add a CSS override
  file to your site configuration, create a ``head-extra.html`` template with the
  following content:

  .. code-block:: mako

    <%namespace name='static' file='../../static_content.html'/>
    <% style_overrides_file = static.get_value('css_overrides_file') %>

    % if style_overrides_file:
      <link rel="stylesheet" type="text/css" href="${static.url(style_overrides_file)}" />
    % endif

  If you already have a ``head-extra.html`` template, you can modify it to
  output this ``<link rel="stylesheet">`` tag, in addition to whatever else you
  already have in that template.
