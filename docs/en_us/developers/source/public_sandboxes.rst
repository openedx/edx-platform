####################
edX Public Sandboxes
####################

EdX maintains a set of publicly-available sandboxes, to allow contributors
to interact with the software without having to set it up themselves.

* `edx.org Sandbox`_ for those looking to try out the software powering edx.org

* `Language Sandboxes`_ for contributors helping to translate OpenEdX into
  various languages, who have a need to see translations "in context" - that is,
  in use on an actual website.


edx.org Sandbox
***************
This sandbox is intended for those looking to try out the software powering
`edx.org <www.edx.org>`_.

The sandbox allows users staff- and student-level access to a copy of the current
version of the edx.org website. This sandbox does not allow access to Studio, the
course-authoring system.

Login by visiting the following url:

* `https://www.sandbox.edx.org/ <https://www.sandbox.edx.org/>`_

You can log in to a staff account using the following credentials:

* username: staff@example.com
* password: edx

You can log in to a student account using one the following credentials.
Each user is enrolled in the demo course with an audit, honor code, or
verified certificate, respectively:

*  username: audit@example.com / honor@example.com / verified@example.com
*  password: edx

Language Sandboxes
******************

These sandboxes are intended for translators who have a need to see
translations "in context" - that is, in use on an actual website.

On edx.org, we only pull down reviewed translations from Transifex. See the
`translation guidelines <https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/i18n_translators_guide.rst#joining-a-review-team>`_
for more details.
 
However, these sandboxes present *all* translations, not just reviewed
translations. This means that you may encounter broken pages as you navigate
the website. If this happens, it is probably because your language contains
broken translations (missing HTML tags, altered {placeholders}, etc). Go
through your translations and see if you can figure out what's broken. Use
`this guide <https://github.com/edx/edx-platform/blob/master/docs/en_us/developers/source/i18n_translators_guide.rst#guidelines-for-translators>`_
to review how to produce non-broken translations.

Accessing The Sandboxes
=======================
There are two language sandboxes, one for right-to-left, aka "RTL", languages
(Arabic, Farsi, Hebrew, and Urdu) and a second one for left-to-right, aka "LTR",
languages.

You can visit the LMS, or learning management system, at:

* LTR Sandbox `http://translation-ltr.m.sandbox.edx.org/ <http://translation-ltr.m.sandbox.edx.org/>`_

* RTL Sandbox `http://translation-rtl.m.sandbox.edx.org/  <http://translation-rtl.m.sandbox.edx.org/>`_

You can also visit Studio (the course authoring platform) at:

* LTR Sandbox `http://studio.translation-ltr.m.sandbox.edx.org/ <http://studio.translation-ltr.m.sandbox.edx.org/>`_

* RTL Sandbox `http://studio.translation-rtl.m.sandbox.edx.org/ <http://studio.translation-rtl.m.sandbox.edx.org/>`_

To access the sandboxes you'll be prompted for a username and password, use these:

* username: edx
* password: translation

Logging In
==========
Language-specific Staff users have been created, which will enable you to access
Studio as well as see instructor-specific pages within the LMS. You'll be able
to log into the sandbox using the following convention:

* username: LANGUAGE_CODE@example.com
* password: edx

So if you are working on Chinese (China), you'll log in with these credentials:

* username: zh_CN@example.com
* password: edx

You can also make new student-level user accounts, which is useful for verifying
translations within the registration flow.

Feel free to mess around in these sandboxes, you can't break anything!


Caveats and Warnings
====================
#. These sandboxes will be updated with new translations and the newest version
   of the edx-platform code roughly once per week.

#. Within the LMS, you can use the language preference widget on the student
   dashboard page to set your language. However, when viewing Studio or when
   viewing the site logged-out, the site will use your browser preference to pick
   which language to display, so make sure your browser is set to the language
   you're translating to.

#. To see a normal edX instance in English (useful for comparing), switch your
   language to English, or visit the `edx.org Sandbox`_.

#. At the moment, the side does not properly work for languages with an ``@``
   symbol in the language code, so for now, those languages cannot use the
   sandbox.

#. If you have a copy of the edx-platform code, you can generate a list of broken
   translations in your language by first pulling down the latest translation files::

     tx pull -l LANGUAGE_CODE

   Replace ``LANGUAGE_CODE`` with your code, eg ``zh_CN``. Next, run the script::

     python i18n/verify.py

   This generates a report of broken translations in your language. This will not, however,
   catch HTML tags that are out of order (ex. ``</b> <b>`` instead of ``<b> </b>``).


We hope you find these sandboxes helpful. If you have any questions, comments, or
concerns, please give us feedback by posting on the
`openedx-translation <https://groups.google.com/forum/#!forum/openedx-translation>`_
mailing list. We'd be happy to hear about any improvements you think we could make!
