..  _ui_bootstrap:

######################
Working with Bootstrap
######################

This topic describes the Bootstrap framework, and how it should be used to
build user interfaces within edX applications. Note that Bootstrap adoption
started after the Ginkgo release, and so this document applies to the edX
master branch and to the forthcoming Hawthorn release.

If you are interested in the rationale for edX choosing Bootstrap, you can
read about the decision in `OEP-16: Adopting Bootstrap
<https://open-edx-proposals.readthedocs.io/en/latest/oep-0016-bp-adopt-bootstrap.html>`_.

.. highlight:: none

***************
Getting Started
***************

Bootstrap is an open source front end component library that is used by many of
the world's most popular applications. It allows for rapid assembly of front end
components using a responsive grid system, a robust component library and easy
to configure theming capabilities to ensure that new components are rendered
consistently. EdX is using `Bootstrap 4`_ which is a reimplemented version using
Sass and that is currently in beta release.

All edX applications should use the `edx-bootstrap`_ package that can be
installed via `npm`_. This package provides two themes (a default Open edX
theme, as well as an edX branded version), and eventually will provide custom
Open edX styles for common patterns.

..  _ui_bootstrap_custom_designs:

*************************
Developing Custom Designs
*************************

Bootstrap provides a large number of components and layouts out-of-the-box, but
there will always be a need to implement custom designs. There are a number of
considerations to take into account when implementing your designs using Sass.

The most important rule is to avoid hard-coding values such as colors and fonts.
Using hard-coded values means that Bootstrap themes will not be able to affect
your styles, and so your new elements will look out of place. Whenever possible
you should instead use the functions and variables provided by Bootstrap to
access theme colors or fonts. See `Bootstrap customization options`_ for more
details.

For example, here is an example of a hard-coded style::

    .my-element {
      font-family: "Open Sans";
      color: #0000ff;
    }

The recommended alternative is as follows::

    .my-element {
      font-family: $font-family-sans-serif;
      color: theme-color("primary");
    }

If you do find the need for a custom color or font that isn't provided by
the edX Bootstrap library, consider first whether it makes sense to contribute
it back so that other applications can use this value too. If you decide to
add a custom value, define it as a variable that can be overridden by a theme by
using the ``!default`` flag. This allows themes to provide a different value
for this variable if they choose. See the Sass documentation for `default flag`_
for more details.

For example::

    $my-custom-color: #0000ff !default;

    .my-element {
      font-family: $font-family-sans-serif;
      color: $my-custom-color;
    }



.. _Bootstrap 4: https://getbootstrap.com/docs/4.0/getting-started/introduction/
.. _Bootstrap customization options: https://getbootstrap.com/docs/4.0/getting-started/options/
.. _default flag: http://sass-lang.com/documentation/file.SASS_REFERENCE.html#Variable_Defaults___default
.. _edx-bootstrap: https://www.npmjs.com/package/@edx/edx-bootstrap
.. _npm: https://www.npmjs.com/
