web-fragments
=============

.. image:: https://img.shields.io/pypi/v/web-fragments.svg
    :target: https://pypi.python.org/pypi/web-fragments/
    :alt: PyPI

.. image:: https://travis-ci.org/edx/web-fragments.svg?branch=master
    :target: https://travis-ci.org/edx/web-fragments
    :alt: Travis

.. image:: http://codecov.io/github/edx/web-fragments/coverage.svg?branch=master
    :target: http://codecov.io/github/edx/web-fragments?branch=master
    :alt: Codecov

.. image:: http://web-fragments.readthedocs.io/en/latest/?badge=latest
    :target: http://web-fragments.readthedocs.io/en/latest/
    :alt: Documentation

.. image:: https://img.shields.io/pypi/pyversions/web-fragments.svg
    :target: https://pypi.python.org/pypi/web-fragments/
    :alt: Supported Python versions

.. image:: https://img.shields.io/github/license/edx/web-fragments.svg
    :target: https://github.com/edx/web-fragments/blob/master/LICENSE.txt
    :alt: License

Overview
--------

The web fragments library provides a Python and Django implementation for
managing fragments of web pages. In particular, this library refactors the
fragment code from XBlock into a standalone implementation.

A Django view subclass called FragmentView is provided which supports three
different ways of rendering a fragment into a page:

* the fragment can be rendered as a standalone page at its own URL
* the fragment can be rendered into another page directly from Django
* the fragment can be returned as JSON so that it can be rendered client-side

The rationale behind this design can be found in `OEP-12`_.

.. _OEP-12: http://open-edx-proposals.readthedocs.io/en/latest/oep-0012.html

The intention is that a client-side implementation will be provided in a
subsequent version. This should provide JavaScript code to request fragements
over AJAX and then dynamically update the current page. This logic will be a
refactoring of the current implementation in edx-platform for rendering XBlocks.
It is also intended that this functionality will enhance the capabilities
around dependency loading.

.. Documentation
.. -------------
..
.. The full documentation is at https://web-fragments.readthedocs.org.

License
-------

The code in this repository is licensed under the AGPL 3.0 unless otherwise
noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome. Please read `Contributing to edX`_ for details.

Note: Even though these guidelines were written with ``edx-platform`` in mind,
they should be followed for Open edX code in general.

.. _Contributing to edX: https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to the Open edX guide to `Getting Help`_.

.. _Getting Help: https://open.edx.org/getting-help


We don't maintain a detailed changelog.  For details of changes, see the
`GitHub commit history`_.

.. _GitHub commit history: https://github.com/edx/web-fragments/commits/master


