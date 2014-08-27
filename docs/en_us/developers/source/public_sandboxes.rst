####################
edX Public Sandboxes
####################

EdX maintains a set of publicly-available sandboxes that allow contributors
to interact with the software without having to set up a local development
environment.

* `edx.org Sandbox`_ for those looking to try out the software powering edx.org.

* `Language Sandboxes`_ for contributors helping to translate Open edX into
  various languages, who have a need to see translations "in context" - that is,
  in use on an actual website.


edx.org Sandbox
***************
This sandbox is intended for those looking to try out the software powering
`edx.org <www.edx.org>`_.

The sandbox provides staff- and student-level access to a copy of the current
version of the edx.org website. This sandbox does not allow access to Studio, the
course-authoring system.

Log in by visiting the following URL:

* `https://www.sandbox.edx.org/ <https://www.sandbox.edx.org/>`_

You can log in to a staff account using the following credentials:

* username: staff@example.com
* password: edx

You can log in to a student account using one the following credentials.
These user accounts represent students enrolled in the demo course with an
audit, honor code, or verified certificate, respectively:

*  username: audit@example.com / honor@example.com / verified@example.com
*  password: edx

Language Sandboxes
******************

These sandboxes are intended for translators who have a need to see
translations "in context" - that is, in use on an actual website.

On edx.org, we only pull down reviewed translations from Transifex. See the
`translation guidelines <https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/i18n_translators_guide.rst#joining-a-review-team>`_
for more details.
 
To help you review and test, these sandboxes present *all* translations, not
just reviewed translations. This means that you may encounter broken pages as
you navigate the website. If this happens, it is probably because some of the
translated strings in your language have errors such as missing HTML tags or
altered {placeholders}. Go through your translations to find and correct these
types of translation errors. Use
`this guide <https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/i18n_translators_guide.rst#guidelines-for-translators>`_
to review how to produce non-broken translations.

Visiting the Sandboxes
======================
There are two language sandboxes, one for right-to-left, aka "RTL", languages
(Arabic, Farsi, Hebrew, and Urdu) and a second one for left-to-right, aka "LTR",
languages. Right now, RTL and LTR cannot be supported on the same installation,
because the CSS needs to be compiled separately (fixing this issue is a task on our
backlog!).

Note: This is our first deployment of our alpha version of RTL language support! If
you have any comments or find any visual bugs, please let us know by posting on the
`openedx-translation <https://groups.google.com/forum/#!forum/openedx-translation>`_
mailing list.

LTR and RTL sandboxes are available for both the LMS, or learning managment system (the part
of the website that students see) and Studio, the course authoring platform.
You can access the LMS at:

* LTR Sandbox `http://translation-ltr.m.sandbox.edx.org/ <http://translation-ltr.m.sandbox.edx.org/>`_

* RTL Sandbox `http://translation-rtl.m.sandbox.edx.org/  <http://translation-rtl.m.sandbox.edx.org/>`_

And you can access Studio at:

* LTR Sandbox `http://studio.translation-ltr.m.sandbox.edx.org/ <http://studio.translation-ltr.m.sandbox.edx.org/>`_

* RTL Sandbox `http://studio.translation-rtl.m.sandbox.edx.org/ <http://studio.translation-rtl.m.sandbox.edx.org/>`_

To access the sandbox servers, you must supply the following username and password:

* username: edx
* password: translation

Logging In To Sandbox Accounts
==============================
To log in to the sandbox for a language, you supply the language code in the
username as follows:

* username: LANGUAGE_CODE@example.com
* password: edx

So if you are working on Chinese (China), you'll log in with these credentials:

* username: zh_CN@example.com
* password: edx

This user account has Course Staff privileges so that you can test Studio and
instructor-specific pages in the LMS.

You can also make new student-level user accounts, which is useful for verifying
translations within the registration flow.

Feel free to test in any way that you want in these sandboxes. Particularly, you are
encourage to make new courses, as well as add and delete course content. The sandboxes
can be reset if anything breaks, and they are completely disconnected from the
production version of the edx.org website.


Caveats and Warnings
====================
#. These sandboxes will be updated with new translations and the newest version
   of the edx-platform code about once per week.

#. We recommend users utilize Chrome or Firefox when using the edX courseware.

#. When you test, make sure that your browser preference is set to the language
   you want to test. When you are logged in to the LMS, you can use the
   language preference widget on the student dashboard page to set or change
   your language. However, when you are viewing Studio, or if you are not yet
   logged in to the LMS, the site uses your browser preference to determine
   what language to display. See `this page on changing your browser's language
   <http://www.wikihow.com/Change-Your-Browser's-Language>`_ if you need help.

#. To see an untranslated edX instance in English, which can be helpful to
   compare to the translated instance, switch your language to English, or
   visit the `edx.org Sandbox`_.

#. At the moment, the site does not properly work for languages with an ``@``
   symbol in the language code, so for now, those languages cannot use the
   sandbox.

#. If you have a copy of the edx-platform code, you can generate a list of broken
   translations in your language by first pulling down the latest translation files::

     tx pull -l LANGUAGE_CODE

   Replace ``LANGUAGE_CODE`` with your code, for example ``zh_CN``.
   See `this page for instructions on how to configure Transifex <https://github.com/edx/edx-platform/wiki/Internationalization-and-localization>`_.

   Next, run the commands::

     paver i18n_generate
     python i18n/verify.py

   This will generate reports of broken translations in your language. This will not, however,
   catch HTML tags that are out of order (ex. ``</b> <b>`` instead of ``<b> </b>``).


We hope you find these sandboxes helpful. If you have any questions, comments, or
concerns, please give us feedback by posting on the
`openedx-translation <https://groups.google.com/forum/#!forum/openedx-translation>`_
mailing list. We'd be happy to hear about any improvements you think we could make!
