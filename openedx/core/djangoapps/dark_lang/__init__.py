"""
Language Translation Dark Launching
===================================

This app adds the ability to launch language translations that
are only accessible through the use of a specific query parameter
(and are not activated by browser settings).

Installation
------------

Add the ``DarkLangMiddleware`` to your list of ``MIDDLEWARE``.
It must come after the ``SessionMiddleware``, and before the ``LocaleMiddleware``.

Run migrations to install the configuration table.

Use the admin site to add a new ``DarkLangConfig`` that is enabled, and lists the
languages that should be released.
"""

# this is the UserPreference key for the currently-active dark language, if any
DARK_LANGUAGE_KEY = 'dark-lang'
