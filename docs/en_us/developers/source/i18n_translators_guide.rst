##############################
Guidelines for Translating edX
##############################

Open edX uses **Transifex**, an open source translation platform, to power
the translation of edX software into different languages. All translations
are hosted at `Transifex.com <https://www.transifex.com/>`_, which provides
a web application allowing translators to write, submit, and manage their
translations.

This page explains how to get started with Transifex, and provides guidelines
for translators to follow when executing translations. For further discussion,
we welcome you to join the `openedx-translation <https://groups.google.com/forum/#!forum/openedx-translation>`_
mailing list.

Getting Started with Transifex
******************************

Contributors wishing to help translate edx-platform and
associated projects can find edX translation projects on 
`Transifex <https://www.transifex.com/organization/open-edx/dashboard>`_.
Follow these steps to become an Open edX translator!

1. Go to `https://www.transifex.com/signup/contributor/ <https://www.transifex.com/signup/contributor/>`_
   and fill out the form to create your free Transifex account, if you don't already
   have one.

2. Once you've set up your account, visit one of the edX projects and request to become
   a translator for your language.
   Projects::
     `edx-platform <https://www.transifex.com/projects/p/edx-platform/>_`
     `edx-comments-service <https://www.transifex.com/projects/p/edx-comments-service/>`_
     `edx-notifier <https://www.transifex.com/projects/p/edx-notifier/>`_

   If your language is listed, click on the language to be brought to the language's page.
   Next, click "Join team" to become part of the translation team for that language.

   If your language is not listed, click "Request language" to start a new translation
   project for your language.

   An edX translation team member will respond to your request within a few days. Once you're
   approved as a member of a translation team, you can begin translating strings!

Using Transifex
===============

Once you are approved as a translator, you can click on any of the resources in the project
to begin translating it. For help documentation on Transifex, see the `Transifex translators
help desk <http://support.transifex.com/customer/portal/topics/414107-translators/articles>`_.



Guidelines for Translators
**************************

First and foremost, if you are uncertain of how to translate a string, we strongly
encourage you to reach out to us and ask for clarification! Please join the
`openedx-translation <https://groups.google.com/forum/#!forum/openedx-translation>`_
mailing list and make a post. We can help clarify the string, and even add a note
clarifying the string, which will help translators working on other language projects.

Translating strings for a website like edX is more complicated than simply translating sentences
from one language to another. Strings in programs sometimes need to have data inserted into them
before being displayed to the user. Data placeholders label the places in the string where the
data will go. Strings can also have markup like HTML included. It's very important to preserve
the placeholders and markup so that the web site will work properly.

Placeholders come in a few different forms. Often, they are named so that data will be placed into
the proper placeholder. Please familiarize yourself with all the different forms to make your
translation successful.

Summary Of Placeholders
=======================
+-------------------------+
| Placeholder Forms       |
+=========================+
| ``{student_name}``      |
+-------------------------+
| ``%(student_name)s``    |
+-------------------------+
| ``<%= student_name %>`` |
+-------------------------+

When dealing with placeholders, you must follow these rules:
* Do Not translate the placeholder (for example, changing ``{day}`` to ``{día}``).
* Do Not alter or remove the punctuation of the placeholder string (for example, changing a ``_`` to a ``-``).
* Do Not alter the capitalization of the placeholder string (for example, changing ``day`` to ``Day``).
* Do Not alter the spacing of the placeholder string (for example, changing ``{day}`` to ``{ day }``).

Please continue reading for more examples of each type of placeholder strings, as well as
an explanation of how to deal with HTML markup.


1. Do **not** alter or translate placeholder strings in between curly braces (``{ }``). Strings
   inside curly braces will be replaced with different strings while the code
   is executing. Changing the content of the curly braces may cause code to break.

   The placeholder string inside of the braces will give you clues as to what type of data will
   be presented in the final string. For example, ``{student_name}`` will be replaced with the name
   of a student, whereas ``{contact_email}`` will be replaced with an email address that users can
   use to contact us. This will give you some context when you are translating sentences with
   placeholders.

   Altering the strings includes: changing, removing, or adding punctuation, changing
   the capitalization, or adding or removing given spacing. So if the placeholder string
   looks like ``{placeholder_string}``, you should not change it at all, eg ``{Placeholder_String}``,
   ``{placeholder-string}``, ``{ placeholder_string }``, ``{placeholder string}``. All of
   these changes have the potential to break the software.

   Examples::

     String: "Welcome back {student_name}!"

     Good translation: "¡Bienvenido {student_name}!"

     Bad translation: "¡Bienvenido {nombre de estudiente}!"
       Do not translate placeholder string - You must use {student_name} exactly as-is.

     Bad translation: "¡Bienvenido {student-name}!"
       Do not alter the placeholder string punctuation - you must use {student_name} exactly as-is.

     Bad translation: "¡Bienvenido {Student_Name}!"
       Do not alter the placeholder string capitalization - you must use {student_name} exactly as-is.

     Bad translation: "¡Bienvenido { student_name }!"
       Do not add additional spacing inside the ``{}`` - you must use {student_name} exactly as-is.

   You may rearrange the order of these strings, depending on the requirements of your language.
   For example, in English the name of the month precedes the day (January 23), wheras in Spanish,
   the day precedes the month (23 de enero).

   Example::

     String: "Today is {month} {day}."

     Good translation: "Hoy es {day} de {month}."


2. Do **not** alter or translate placeholder strings that begin with a ``%``, then have a string
   inside parenthesis, and then conclude with an 's' or 'd'. You must preserve the whole form.

   As in the previous example, you must not add, change, or remove punctuation, change capitalization,
   or add in new spacing.

   Examples::

     String: "Welcome back %(student_name)s!"

     Good translation: "¡Bienvenido %(student_name)s!"

     Bad translation: "¡Bienvenido %(nombre de estudiente)s!"
       Do not translate placeholder strings - You must use %(student_name)s exactly as-is.

     Bad translation: "¡Bienvenido %(student-name)s!"
       Do not alter the placeholder string punctuation - you must use %(student_name)s exactly as-is.

     Bad translation: "¡Bienvenido %(Student_Name)s!"
       Do not alter the placeholder string capitalization - you must use %(student_name)s exactly as-is.

     Bad translation: "¡Bienvenido %( student_name )s!"
       Do not add additional spacing inside the ``()`` - you must use %(student_name)s exactly as-is.

     Bad translation: "¡Bienvenido (student_name)!"
       Do not remove the '%' or 's' - you must use %(student_name)s exactly as-is.

   You may rearrange the order of these strings, depending on the requirements of your language.
   For example, in English the name of the month precedes the day (January 23), wheras in Spanish,
   the day precedes the month (23 de enero).

   Example::

     String: "Today is %(month)s %(day)d."

     Good translation: "Hoy es %(day)d de %(month)s."


3. Do **not** alter or translate placeholder strings that appear within a ``<%= %>`` block. Placeholder
   strings in this format look like this: ``<%= student_name %>``.

   As in the previous examples, you must not add, change, or remove punctuation, change capitalization,
   or add in new spacing.

   Examples::

     String: "Welcome back <%= student_name %>!"

     Good translation: "¡Bienvenido <%= student_name %>!"

     Bad translation: "¡Bienvenido <%= nombre de estudiente %>!"
       Do not translate placeholder strings - You must use <%= student_name %> exactly as-is.

     Bad translation: "¡Bienvenido <%= student-name %>!"
       Do not alter the placeholder string punctuation - you must use <%= student_name %> exactly as-is.

     Bad translation: "¡Bienvenido <%= Student_Name %>!"
       Do not alter the placeholder string capitalization - you must use <%= student_name %> exactly as-is.

     Bad translation: "¡Bienvenido < % =  student_name % >!"
       Do not add additional spacing inside the ``<%= %>`` - you must use <%= student_name %> exactly as-is.

     Bad translation: "¡Bienvenido <student_name>!"
       Do not remove or change the '<%=' or '%>' - you must use <%= student_name %> exactly as-is


4. Do **not** alter or translate `HTML markup tags <https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Introduction>`_.
   You should translate the text that is between the tags. HTML markup tags begin and end with ``<``
   and ``>`` characters.

   Spacing is especially important. Adding spaces in an HTML tag (eg changing ``</a>`` to ``</ a>``)
   may break the website.

   Examples::

     String: "If you have a general question about {platform_name} please email 
     <a href="mailto:{contact_email}">{contact_email}</a>."

     Good translation: "{platform_name}에 대해 일반적인 질문이 있으면 
       <a href="mailto:{contact_email}">{contact_email}</a>로 이메일 주십시요."

     Bad translation: "{platform_name}에 대해 일반적인 질문이 있으면 
       {contact_email}로 이메일 주십시요."

       Please do not remove the HTML tags.

     Bad translation: "{platform_name}에 대해 일반적인 질문이 있으면 
       <a href="흔한:{contact_email}">{contact_email}</a>로 이메일 주십시요."

       Do not translate the HTML tags. Please use the given HTML tags.

     Bad translation: "{platform_name}에 대해 일반적인 질문이 있으면 
       <b>{contact_email}</b>로 이메일 주십시요."

       Do not change the HTML tags to something new. Please use the given HTML tags.

     Bad translation: "{platform_name}에 대해 일반적인 질문이 있으면 
       < a href = " mailto : {contact_email} " > {contact_email} < / a >로 이메일 주십시요."

       Do not add additional spacing to the HTML tags. Please use the given HTML tags.
