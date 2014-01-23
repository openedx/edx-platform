Language Translation Dark Launching
===================================

This app adds the ability to launch language translations that
are only accessible through the use of a specific query parameter
(and are not activated by browser settings).

Installation
------------

Add the ``.DarkLangMiddleware`` to your list of ``MIDDLEWARE_CLASSES``.
It must come after the ``SessionMiddleware``, and before the ``LocaleMiddleware``.

Add the ``RELEASED_LANGUAGES`` setting to your settings file. This
should be a list of all language codes which can be selected via a
user's browser settings.