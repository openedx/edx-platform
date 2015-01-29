.. _Accessibility Guideline for Developers:

#######################
edX Accessibility Guide
#######################

EdX measures and evaluates accessibility using the World Wide Web Consortium's
`Web Content Accessibility Guidelines (WCAG) 2.0 <http://www.w3.org/TR/WCAG/>`_
(Dec. 11, 2008). All features that you merge into edX repositories are expected
to `conform <http://www.w3.org/TR/WCAG20/#conformance>`_ to `Level AA
<http://www.w3.org/TR/WCAG20/#cc1>`_ of this specification. This guide is
intended to extend the guidance available in WCAG 2.0, with a focus on features
frequently found in the Open edX platform as well as in Learning and Content
Management Systems in general.

************
Introduction
************

The core mission of edX is to expand access to education for everyone. We expect
any user interfaces that are developed for the Open edX platform to be usable by
everyone, regardless of any physical limitations that they might have. The Open
edX platform is used every day by people who might not be able to see or hear,
or who might not be able to use traditional modes of computer interaction such
as the mouse or keyboard. 

Understanding a few core concepts about how people with disabilities use the web
and web applications should give you more context for applying the guidance in
this document.

* People without vision, as well as those with neurological conditions that
  prevent precise hand-eye coordination, cannot use a mouse.

* People with mobility impairments might use custom keyboards or keyboard
  emulators.

* Some people rely on speech to interact with web applications and need to be
  able to address interactive elements.

* People who cannot hear or hear well require visible text captions, or an
  equivalent visual cue, for any audible content.

* Many people with disabilities use "`Assistive Technology
  <http://www.w3.org/TR/WCAG20/#atdef>`_" (such as screen readers) to interact with their computers, web browsers, and web applications. Users may customize
  their operating system, browser or web page display properties to make web
  applications easier for them to use. For example, they might increase the font size in their displays, reverse or increase contrast, or remove images. 

* In order that assistive technologies can provide the maximum information to
  users, anything in a user interface that is conveyed visually (such as the
  element with focus, an element's role, its current state, and other properties)
  must also be conveyed programmatically. This information is often included when
  you use native HTML5 elements.

Keep these core concepts in mind when you develop user interfaces, so that they
can truly be used by everyone. More information is available from the W3C's Web
Accessibility Initiative's `How People with Disabilities Use the Web: Overview
<http://www.w3.org/WAI/intro/people-use-web/Overview.html>`_.


****************************
Accessibility Best Practices
****************************

The following sections cover some best practices and tips to keep in mind as you
develop user interfaces that are WCAG 2.0 compliant.

* :ref:`Use semantic markup`
* :ref:`Avoid using CSS to add content`
* :ref:`Include title attributes for all iframe elements`
* :ref:`Make sure form elements have labels`
* :ref:`Include informational labels for all links and interactive controls`
* :ref:`Use WAI ARIA to create accessible widgets`
* :ref:`Manage focus for popups`
* :ref:`Inform users when content changes dynamically`
* :ref:`Hide or expose content to targeted audiences`
* :ref:`Make images accessible`
* :ref:`Choose colors that meet minimum contrast ratios`
* :ref:`Test your code for accessibility`


.. _Use semantic markup:

*******************
Use semantic markup
*******************

The role, state, and associated properties of an element are exposed to users of
assistive technologies either directly through the DOM or through the
Accessibility API. If you use elements for purposes other than their intended
purposes, you can "break" features that are designed to make web applications
easier to use, resulting in confusion when expected behaviors are not available.
For example, the role, state, or associated properties of an element might be
incorrectly reported when you use an element in a way that it was not designed
to be used, causing confusion for users who rely on assistive technologies.

If the semantics and behavior you need already exist in a native HTML5 element,
you should use that element. Do not use an element because of its default style
or because it provides a convenient styling hook. Here are some common examples.

-------
Buttons
-------

If you want a button, use the ``<button>`` element. Do not use a ``<div>`` that
looks and behaves like a button.

----------
Checkboxes
----------

If you want a checkbox, use the ``<input type=checkbox>`` element. Do not try to
recreate states and properties that are included with the native element, such
as focus or state. If you attempt to do so, more than likely you will not fully
replicate all of them. Native checkbox elements include a toggle for checked
state upon ``space`` or ``enter`` keypresses, exposing its label and
"`checkedness <http://www.w3.org/TR/html5/forms.html #concept-fe-checked>`_" to
the Accessibility API.

--------
Headings
--------

Use the appropriate levels of headings (``<h1>`` - ``h6>``) to denote a logical
hierarchical order of content. Do not use headings as stylistic markup (for
their physical size or appearance).

-----
Lists
-----

Use ordered lists (``<ol>``) only when you are marking up a collection of
related items whose order in the list if important. Use unordered lists
(``<ul>``) only when you are marking up a collection of related items. Screen
readers provide extra feedback and functionality for lists and other elements
with semantic importance. It can be confusing or cumbersome when this feedback is
inaccurately reported.


.. _Avoid using CSS to add content:

******************************
Avoid using CSS to add content
******************************

CSS-generated content can cause many accessibility problems. Since many screen
readers interact with the DOM, they are not exposed to content generated by CSS,
which does not live in the DOM. There is currently no mechanism for adding
alternative content for images added using CSS (either background images or
pseudo elements).

Many developers think that providing screen reader-only text can be used to
solve this. However, images added using this technique will not be rendered to
users who have high contrast mode enabled on their operating systems. These
users are likely not using screen readers, so they cannot access the visible
icon, or the screen reader text.

Content injected into the DOM using JavaScript is more accessible than content added using CSS.

When adding images that represent important navigational or information
elements, use ``<img>`` elements with appropriate ``alt`` attributes. For more
information about making images accessible, see :ref:`Make images accessible`.
   

.. _Include title attributes for all iframe elements:

***********************************************************************
Include a descriptive ``title`` attribute for all ``<iframe>`` elements
***********************************************************************

Use the ``title`` attribute to provide a description of the embedded content to
help users decide whether or not they would like to interact with this content.
It is possible that ``<iframe>`` titles are presented out of context (such as in
a list within a dialog box), so choose title text that will make sense when it
is exposed out of context.


.. _Include informational labels for all links and interactive controls:

***********************************************************************
Include labels for all links and interactive controls that make sense out of context
************************************************************************

Label text for all links and interactive controls should make sense out of
context. Screen reader users have the option of listing and navigating links and
form controls out of the context of the page. When a page contains vague and
non- unique text such as **Click here** or **More...**, the purpose of these
links is not clear without the context of surrounding text.


.. _Make sure form elements have labels:

**************************************
Make sure form elements have labels
**************************************

All form elements must have labels, either using the `label element
<http://www.w3.org/TR/html5/forms.html#the-label-element>`_ or the `aria-label
<http://www.w3.org/TR/wai-aria/states_and_properties#aria-label>`_ or `aria-
labelledby <http://www.w3.org/TR/wai-aria/states_and_properties#aria-
labelledby>`_ attributes.

Sighted users have the benefit of visual context. It is usually quite obvious to
them what the purpose is of a given form field, based on physical proximity of
descriptive text or other visual cues. However, to a user with a vision
impairment, who does not have the benefit of visual context, these relationships
are not obvious. Users who rely on speech to interact with their computers also
need a label for addressing form elements. Correctly using the ``<label>``
element programmatically associates text with a given form element, which can be
spoken to the user upon focus, or used to address the form element.

.. _note:: Screen readers often enter "forms processing mode" when they
   encounter a form. This mode temporarily disables all keyboard shortcuts
   available to users so that key presses are passed through to the control,
   with the exception of ``TAB`` which, moves focus from one form field to the
   next. This means that context-sensitive help provided for form fields (such
   as UI help text adjacent to the form field) is not likely to be encountered
   by screen reader users. To remedy this situation, add an `aria- describedby
   <http://www.w3.org/TR/wai-aria/states_and_properties#aria- describedby>`_
   attribute to the input that references the help text. Doing so
   programmatically links the help text to the form control so that users can
   access it while their screen readers are in forms processing mode.


.. _Use WAI ARIA to create accessible widgets:

********************************************************************
Use WAI-ARIA to create accessible widgets or enhance native elements
********************************************************************

In some cases, native HTML5 elements will not provide the behavior or style
options that you want. If you develop custom HTML or JavaScript widgets, make
sure you add all necessary role, state, and property information for each
widget, so that it can be used by users of assistive technology. 

WAI-ARIA (Web Accessibility Initiative - Accessible Rich Internet Applications)
is a technical specification published by the World Wide Web Consortium (W3C)
that specifies how to increase the accessibility of web pages. 

When you develop custom widgets, use WAI-ARIA to ensure that your custom
controls are accessible, and consider the following points.

* Is the `role <http://www.w3.org/TR/wai-aria/roles>`_ of the widget properly
  identified?

* Can a user focus on and interact with your widget using the keyboard alone?
  
* When the state or some other property of your widget changes, are those
  changes conveyed to users of assistive technology using aria-attributes?


.. _note:: Adding an ARIA ``role`` overrides the native role semantics reported
   to the user from the Accessibility API. ARIA indirectly affects what is
   reported to a screen reader or other assistive technology. Adding an ARIA
   ``role`` to an element does not add the behaviors or attributes to that
   element. You have to do that yourself.


ARIA attributes can also be used to enhance native elements by adding helpful
information specifically for users of assistive technology. Certain sectioning
elements (such as ``<nav>`` and ``<header>``) as well as generic ones (such as
``<div>`` with "search", "main" or "region" roles defined), receive special
behaviors when encountered by assistive technology. Most screen readers
announce when a user enters or leaves one of these regions, allow direct
navigation to the region, and present the regions to a user in a list that they
can use to browse the page out of context. Because your pages are likely to have
multiple ``<nav>`` elements or ``<divs>`` with a role of region, it is important
to use the ``aria-label`` attribute with a clear and distinct value to
differentiate between them.


---------------------------------------------------------------
Example: Adding descriptive labels to HTML5 structural elements
---------------------------------------------------------------

	<!-- the word "Navigation" is implied and should not be included in the label -->
	<nav aria-label="Main">
	...
	</nav>
	
	<nav aria-label="Unit">
	...
	</nav>
	
	<div role="search" aria-label="Site">
	...
	</div>
	
	<div role="search" aria-label="Course">
	...
	</div>

--------------------------------
Some cautions for using WAI-ARIA
--------------------------------

The following sections outline specific cases in which you have to be careful
using WAI-ARIA.

* Setting ``role="presentation"`` strips away all of the semantics from a native
  element.
  
* Setting ``role="application"`` on an element passes all keystrokes to the
  browser for handling by scripts. In this case, all keyboard shortcuts   provided
  by screen readers are disabled. You should only use ``role="application"`` if
  you can provide support for all of the application's functions via the
  keyboard as well as the roles, states, and properties for all of its child
  elements.
  
* Setting ``aria-hidden="true"`` removes an element from the Accessibility API,
  making it invisible to a user of assistive technology. For elements that you
  intend to hide from all users, setting the CSS property ``display:none;`` is
  sufficient. It is unnecessary to also set ``aria-hidden="true"``. Once the
  content is revealed by changing the display property, it is too easy to forget
  to toggle the value of ``aria-hidden``.

  There are legitimate use cases for ``aria-hidden``, for example when you use an
  icon font that has accessible text immediately adjacent to it. Icon fonts can be
  focused on by certain screen readers, and will remain silent upon focus This can
  lead screen reader users to suspect they are missing important content. Some
  screen readers display what is being spoken on the screen, which helps users
  with certain cognitive disabilities. Icon fonts will often be rendered as a
  nondescript glyph in these cases. It is useful to remove them with ``aria-
  hidden``, to prevent exposing a screen reader user to redundant information when
  information is available in an accessible format as well as a less than
  accessible format.


Additional considerations for developing custom widgets are covered in `General
steps for building an accessible widget <http://www.w3.org/TR/wai-aria-
practices/#accessiblewidget>`_. 

Specific considerations for common widgets are covered in `WAI-ARIA 1.0
Authoring Practices - Design Patterns <http://www.w3.org/TR/2013/WD-wai-aria-
practices-20130307/#aria_ex>`_. 

A quick reference list of Required and Supported ARIA attributes by role is
available in the `ARIA Role, State, and Property Quick Reference
<http://www.w3.org/TR/aria-in-html/#aria-role-state-and- property-quick-
reference>`_

.. _Manage focus for popups:

***************************************
Manage the focus for pop-ups
***************************************

Do not forget to manage focus on pop-ups. Whenever a control inserts interactive
content into the DOM or reveals previously hidden content (for example, pop-up
menus or modal dialog boxes), you must move focus to the container. While the
focus is within the menu or dialog box, keyboard focus should remain trapped
within its bounds. Clicking the **Esc** key or the **Save** or **Cancel** button
should close and exit the region and return focus to the element that triggered
it.

Note that ``<div>`` and other container elements are not natively focusable. If
you want to move focus to a container you must set a ``tabindex="-1"`` attribute
for that container. You should also define an ``aria-label`` or ``aria-
labelledby`` attribute that identifies the purpose of the container.


.. _Inform users when content changes dynamically:

*********************************************
Inform users when content changes dynamically
*********************************************

If a user action or script updates the content of a page dynamically, you should
add the ``aria-live="polite"`` attribute to the parent element of the region
that changes. Doing so ensures that the contents of the element are read to a
screen reader user, even though the element does not currently have focus. This
method is not intended to be used when the region contains interactive elements.


.. _Hide or expose content to targeted audiences:

********************************************
Hide or expose content to targeted audiences
********************************************

Content that enhances the experience for one audience might be confusing or
encumber a different audience. For instance, a **Close** button that looks like
``X`` will be read by a screen reader as the letter X, unless you hide it from
the Accessibility API. 

To visibly hide content that should be read by screen readers, edX makes a CSS
``class="sr"`` available to expose content only to screen reader users. In the
following example, a sighted user see only the X, while a screen reader user
hears only "Close".

  ::
<a href="#"> 
<span aria- hidden="true">X</span> 
<span class="sr">Close</span>
</a>


.. _Make images accessible:

**********************
Make images accessible
**********************

You can make images accessible by using the ``alt`` attribute for each image, or
by providing a text alternative for an image.

---------------------
Text alternatives
---------------------

A text alternative is text that users who are unable to view or use non-text
content can access in place of the non-text content (such as images, charts,
applets, audio files, and so on).

Text alternatives must be "programmatically determinable". This means that the
text must be able to be read and used by the assistive technologies (and the
accessibility features in browsers) that people with disabilities use.

Text alternatives must also be "programmatically associated" with the non-text
content. This means that users must be able to use assistive technology to find
the alternative text (that they can use) when they land on the non-text content
(that they cannot use).

All images require a `text alternative <http://www.w3.org/TR/WCAG20/#text-
altdef>`_ . The only exceptions to this rule are purely decorative images or
images that have text alternatives adjacent to them.

--------------
Alt attributes
--------------

Regardless of whether or not an image requires a text alternative, *all*
``<img>`` elements require an ``alt`` attribute, even if the value of that
attribute is ``""`` (NULL). If your image is purely decorative, or has a text
alternative immediately adjacent to it, use a NULL alt attribute: ``alt=""``.

If an ``<img>`` element does not have a NULL alt attribute, you should make sure
that the value you use in its alt attribute provides useful information to users
who rely on screen readers. Screen readers will expose the path to the image as
a last resort, if an alt attribute value does not exist.


------------------------------------
Best practices for non-text elements
------------------------------------

Providing *useful* text alternatives or alt attribute values is more difficult
than it sounds. Ask yourself questions about the purpose of your image to
determine what would be most useful to the user.

* Is your image the only content of a link or form control?

    Your ``alt`` attribute should describe the destination of the link, or the
    action that will be performed. For example, a "Play" icon should have a text
    alternative such as "Play the 'Introduction to Linux' course video", rather
    than "Right-pointing triangle".
    
* Does your image contain text? The vast majority of images of text should
  include the verbatim text as the value of the ``alt`` attribute. Here are some
  examples of exceptions.
  
    * If yes, and if the same text appears adjacent to or near the image in the
      DOM, use a "NULL" value in the alt attribute, otherwise a screen reader is
      exposed to the same content twice.
    
    * If yes, and if the text within the image is there simply for visual effect
      (such as a skewed screenshot of computer code), use a "NULL" value in the
      alt attribute.
	  
* Does your image contribute meaning to the current page or context?
  
    * If yes, and if the image is a simple graphic or photograph, the alt
      attribute should briefly describe the image in a way that conveys the same
      meaning that a sighted person would obtain from viewing the image. Context
      is important. A detailed description of a photograph is rarely useful to
      the user, unless it is in the context of a photography or art class.
	  
    * If yes, and if the image is a graph or complex piece of information,
      include the information contained in the image elsewhere on the page. The
      alt attribute value should give a general description of the complex image. You
      can programmatically link the image with the detailed information using ``aria-
      describedby``.
	
A very pragmatic guide on providing useful text alternatives is included in the
`HTML5 specification (4.7.1.1) <http://www.w3.org/TR/html5/embedded-
content-0.html#alt>`_ and includes a variety of example images and appropriate
text alternatives.


.. _Choose colors that meet minimum contrast ratios:

**********************************************************
Choose colors that meet WCAG 2.0's minimum contrast ratios
**********************************************************

A minimum contrast between foreground and background colors is critical for
users with impaired vision. You can `check color contrast ratios
<https://leaverou.github.io/contrast-ratio/>`_ using any number of tools
available free online.


.. _Test your code for accessibility:

********************************
Test your code for accessibility
********************************

The only way to determine if your feature is fully accessible is to manually
test it using assistive technology; however, there are a number of automated
tools you can use to perform a self assessment. Automated tools might report
false positives and might not catch every possible error, but they are a quick
and easy way to detect the most common mistakes.

These are some automated tools for accessibility testing.

* `WAVE Accessibility Toolbar <http://wave.webaim.org/toolbar/>`_
  (Chrome/Firefox)
  
* `Web Developer Toolbar <https://addons.mozilla.org/en-US/firefox/addon/web-
  developer/>`_ (Firefox)
  
* `Chrome Accessibility Developer Tools
  <https://chrome.google.com/webstore/detail /accessibility-
  developer-t/fpkknkljclfencbdbgkenhalefipecmb>`_

* Your keyboard


To test your feature using a screen reader, you can use the following free
options.

* Voiceover (Command + F5 on Mac)
  
* `ChromeVox <http://www.chromevox.com>`_ (Screen reader for Chrome)
  
* `NVDA <http://www.nvaccess.org/download/>`_ (Screen Reader for Windows - FOSS)
  
* `JAWS <http://www.freedomscientific.com/Downloads/ProductDemos>`_ (Screen
  Reader for Windows - Commercial but free to use in 40 minute demo mode)
  

