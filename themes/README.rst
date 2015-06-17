If you want to continue using the Stanford theming system, there are a few
changes you'll need to make.

Create the following new files in the ``sass`` directory of your theme:

* lms-main.scss
* lms-main-rtl.scss
* lms-course.scss
* lms-course-rtl.scss
* lms-footer.scss
* lms-footer-rtl.scss

The contents of each of these files will be very similar. Here's what
``lms-main.scss`` should look like:

.. code-block::

    $static-path: '../../../edx-platform/lms/static';
    @import 'lms/static/sass/lms-main';
    @import '_default';

Each file should set the ``$static-path`` variable to a relative path that
points to the ``lms/static`` directory inside of ``edx-platform``. Then,
it should ``@import`` the sass file under ``lms/static/sass`` that matches
its name: ``lms-footer.scss`` should import ``lms/static/sass/lms-footer``,
for example. Finally, the file should import the ``_default`` name, which
refers to the ``_default.scss`` Sass file that should already exist in your
Stanford theme directory.
