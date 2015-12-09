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

Most CSS styling in Open edX is done with Sass files compiled to CSS.  You can
override individual settings by creating a new Sass file that uses the existing
file, and overrides the few settings you want.

For example, to change the fonts used throughout the site, you can create an
``lms/static/sass/_overrides.scss`` file with the change you want::

    $sans-serif: 'Helvetica';

The variables that can currently be overridden are defined in
``lms/static/sass/base/_variables.scss``.

**Note:** We are currently in the middle of a re-engineering of the Sass
variables.  They will change in the future.  If you are interested, you can see
the new development in the `edX Pattern Library`_.

.. _edX Pattern Library: http://ux.edx.org/

Then create ``lms/static/sass/lms-main.scss`` to use those overrides, and also
the rest of the definitions from the original file::

    // Our overrides for settings we want to change.
    @import 'overrides';

    // Import the original styles from edx-platform.
    @import 'lms/static/sass/lms-main';

Do this for each .scss file your site needs.


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

You should **not** use the following names in your comprehensive theme:

* ``themable-footer.html``

If you look at the ``main.html`` template file, you will notice that it includes
``header.html`` and ``themable-footer.html``, rather than ``footer.html``.
You might be inclined to override ``themable-footer.html`` as a result. DO NOT
DO THIS. ``themable-footer.html`` is an additional layer of indirection that
is necessary to avoid breaking microsites, which also refers to a file named
``footer.html``. The goal is to eventually make comprehensive theming do
everything that microsites does now, and then deprecate and remove microsites
from the codebase. At that point, the ``themable-footer.html`` file will go
away, since the additional layer of indirection will no longer be necessary.

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

#.  Otherwise, edit the /edx/app/edxapp/lms.env.json file to add the
    ``COMPREHENSIVE_THEME_DIR`` value::

        "COMPREHENSIVE_THEME_DIR": "/full/path/to/my-theme",

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

    $ paver update_assets lms --settings=aws

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
  config value in your microsite configuration.

* If you don't want the Google Analytics JavaScript to be output at all in your
  microsite, set the "GOOGLE_ANALYTICS_ACCOUNT" config value to the empty string.
  If you want to customize the way that Google Analytics is loaded, set the
  "GOOGLE_ANALYTICS_ACCOUNT" config value to the empty string, and then load
  Google Analytics yourself (with whatever customizations you want) in your
  ``head-extra.html`` template.

* The ``css_overrides_file`` config value is now ignored. To add a CSS override
  file to your microsite, create a ``head-extra.html`` template with the
  following content:

  .. code-block:: mako

    <%namespace name='static' file='../../static_content.html'/>
    <%! from microsite_configuration import microsite %>
    <% style_overrides_file = microsite.get_value('css_overrides_file') %>

    % if style_overrides_file:
      <link rel="stylesheet" type="text/css" href="${static.url(style_overrides_file)}" />
    % endif

  If you already have a ``head-extra.html`` template, you can modify it to
  output this ``<link rel="stylesheet">`` tag, in addition to whatever else you
  already have in that template.
