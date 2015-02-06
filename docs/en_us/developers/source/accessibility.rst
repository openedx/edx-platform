#######################
edX Accessibility Guide
#######################

EdX measures and evaluates accessibility using the World Wide Web Consortium's `Web Content Accessibility Guidelines (WCAG) 2.0 <http://www.w3.org/TR/WCAG/>`_ (Dec. 11, 2008). All features merged into edX are expected to `conform <http://www.w3.org/TR/WCAG20/#conformance>`_ to `Level AA <http://www.w3.org/TR/WCAG20/#cc1>`_ of this specification. This guide is intended to extend the guidance available in WCAG 2.0, with a focus on features frequently found in the Open edX platform as well as Learning and Content Management Systems in general.

Introduction
************

The core mission of edX is to expand access to education for everyone. We expect that any user interfaces that are developed for the Open edX platform should be usable by everyone, regardless of any physical limitation they may have. The Open edX platform is used every day by people who might not be able to see, hear or might not have the dexterity to use traditional modes of computer interaction (such as the mouse). Understanding a few core concepts about how people with disabilities use the web and web applications should make the guidance in this document a little easier to understand.

* A person without vision cannot use a mouse and neither can those with neurological conditions that prevent the kind of precise hand-eye coordination required to use a mouse.
* Many people with disabilities use "`Assistive Technology <http://www.w3.org/TR/WCAG20/#atdef>`_" (such as screen readers) to interact with their computers, web browsers, and web applications.
* Anything conveyed visually (such as an element's role, state or other properties) must also be conveyed programmatically so that assistive technologies know the element's role, what state it's currently in and how users can interact with it. *Protip:* This information often comes for free when you use native HTML5 elements.
* Many people with mobility impairments use custom keyboards or keyboard emulators.
* Some people rely on speech to interact with web applications and need to be able to address interactive elements.
* Someone who cannot hear or hear well requires visible text captions for any audible content or an equivalent visual cue.
* Users may customize their operating system, browser or web page display properties to make web applications easier for them to use (like reversing contrast, increasing font size, or removing images). 

These are just a few core concepts developers need to keep in mind when developing user interfaces that work for everyone. More information is available from the W3C's Web Accessibility Initiative's `How People with Disabilities Use the Web: Overview <http://www.w3.org/WAI/intro/people-use-web/Overview.html>`_.

Use semantic markup
*******************

The role, state and associated properties of an element are exposed to users of Assistive Technology either directly through the DOM or through the Accessibility API. Using elements for purposes other than the ones they are intended for have the consequence of falsely reporting the role, state and associated properties of the element to these users. This breaks features designed to make web apps easier to use and can often result in confusion when expected behaviors are not available.

If the semantics and behavior you need already exist in a native HTML5 element, you should use that element:  

* If you want a button, use the ``<button>`` element and not a ``<div>`` that looks and behaves like a button. 
* If you want a checkbox, you should use an ``<input type=checkbox>`` and not try to recreate the states and properties you get with the native element for free. Chances are, you will not fully replicate all of them, i.e. making it focusable, toggling its checked state upon ``space`` or ``enter`` keypresses, exposing its label and  "`checkedness <http://www.w3.org/TR/html5/forms.html#concept-fe-checked>`_" to the Accessibility API (did you know a checkbox can be in an intermediate state?)

Don't use an element because of its default style or because it provides a convenient styling hook:

* Are you choosing the Heading level (``<h1>`` - ``h6>``) because of its physical size or appearance?  Heading levels should be determined by their logical order in the hierarchical structure of the document.
* Are you really marking up a list of items, or are you using an ``<ul>`` as a styling hook?  Unordered lists should only be used when marking up a collection of related items.  Ordered lists are for a collection of related items where their order in the list is of importance.  Screen readers provide extra feedback and functionality for lists and other elements with semantic importance.  It can confusing or cumbersome when this feedback is inaccurately reported.

Make Your Images Accessible
***************************

All images require a `text alternative <http://www.w3.org/TR/WCAG20/#text-altdef>`_ with the exception of any image that is purely decorative or has a text alternative adjacent to it. Regardless of whether or not an image element requires a text alternative, *all* ``<img>`` elements require an ``alt`` attribute, even if the value of that attribute is ``""`` (NULL). Because an author error should not prevent a screen reader user from using a web site, screen readers will expose the path/to/the/image as a last resort, in an effort to provide some useful information to the user regarding the purpose of the image. If your image is purely decorative, or has a text equivalent immediately adjacent to it, use a NULL alt attribute i.e. ``alt=""``.

Providing a *useful* text alternative is more nuanced than it sounds. Asking yourself questions about the purpose of your image can usually help you determine what would be most useful to the user:

* Is your image the only content of a link or form control?
    * Your ``alt`` attribute should describe the destination of the link, or the action that will be performed. A "Play" icon should have a text equivalent similar to "Play the 'Introduction to Linux' course video", not "Right pointing triangle."
* Does your image contain text?
    * Is the same text adjacent or near the image in the DOM?
		* Use a "NULL" value, otherwise a screen reader is exposed to the content twice.
	* Is the text there simply for visual effect? (like a skewed screenshot of computer code)
		* Use a "NULL" value
	* The vast majority of images of text should include the verbatim text as the value of the ``alt`` attribute.
* Does your image contribute meaning to the current page or context?
	* Yes, and it’s a simple graphic or photograph: the alt attribute should briefly describe the image in a way that conveys the same meaning. Context is important. A detailed description of a photograph is rarely useful to the user, unless it is in the context of a photography or art class.
    * Yes, and it’s a graph or complex piece of information: include the information contained in the image elsewhere on the page. The alt attribute should give a general description of the complex image. You can programmatically link the image with the detailed information using ``aria-describedby``.
	
A very pragmatic guide on providing useful text alternatives is included in the `HTML5 specification (4.7.1.1) <http://www.w3.org/TR/html5/embedded-content-0.html#alt>`_ and includes a variety of example images and appropriate text alternatives.

Use labels on all form elements
*******************************

All form elements must have labels, either using the `label element <http://www.w3.org/TR/html5/forms.html#the-label-element>`_ or the `aria-label <http://www.w3.org/TR/wai-aria/states_and_properties#aria-label>`_ or `aria-labelledby <http://www.w3.org/TR/wai-aria/states_and_properties#aria-labelledby>`_ attributes.

Sighted users have the benefit of visual context. It's often quite obvious what text identifies the purpose of a given form field based on physical proximity or other visual cues. However, to a user with a vision impairment, who does not have the benefit of visual context, these relationships are not obvious. Users who rely on speech to interact with their computers also need a label for addressing form elements. Correctly using the ``<label>`` element programmatically associates text with a given form element, which can be spoken to the user upon focus, or used to address the form element.

*Protip:* Screen reader users often enter "forms processing mode" when they encounter a form. This temporarily disables all of the keyboard shortcuts available to them so key presses are actually passed through to the control, with the exception of ``TAB`` which will move focus from one form field to the next. This means that context sensitive help provided for form fields (like help text adjacent to the form field) is not likely to be encountered by these users. Add an `aria-describedby <http://www.w3.org/TR/wai-aria/states_and_properties#aria-describedby>`_ attribute to the input referencing this text. This programmatically links the text to the form control so the user can access it while in forms processing mode.

Use WAI-ARIA to create accessible widgets or enhance native elements
********************************************************************

There will be times when native HTML5 elements just don't give you the behavior or style options you need or desire. When developing custom HTML/JS widgets make sure you add all the necessary role, state and property information so that your widget can be used by users of assistive technology:

* Is the `role <http://www.w3.org/TR/wai-aria/roles>`_ of the widget properly identified?
* Can a user focus on and interact with your widget using the keyboard alone?
* When the state or other properties of your widget change, are those changes conveyed to users of assistive technology using aria-attributes?

Additional considerations for developing custom widgets are covered in `General steps for building an accessible widget <http://www.w3.org/TR/wai-aria-practices/#accessiblewidget>`_. Specific considerations for common widgets are covered in `WAI-ARIA 1.0 Authoring Practices - Design Patterns <http://www.w3.org/TR/2013/WD-wai-aria-practices-20130307/#aria_ex>`_. A quick reference list of Required and Supported ARIA attributes by role is available in the `ARIA Role, State, and Property Quick Reference  <http://www.w3.org/TR/aria-in-html/#aria-role-state-and-property-quick-reference>`_

*Protip:* Adding an ARIA ``role`` overrides the native role semantics reported to the user from the Accessibility API. ARIA indirectly affects what is reported to a screen reader or other assistive technology. Adding an ARIA ``role`` to an element does not add the behaviors or attributes to that element. You have to do that yourself. 

ARIA attributes can also be used to enhance native elements by adding helpful information specifically for users of assistive technology. Certain sectioning elements, like ``<nav>`` and ``<header>``  as well as generic ones like ``<div>`` with roles defined ("search", "main" or "region") receive special behaviors when encountered by assistive technology. Most screen readers will announce when the user enters or leaves one of these regions, allow direct navigation to the region and will present the regions to the user in a list they can use to browse the page out of context. Since your pages are likely to have multiple ``<nav>`` elements or ``<divs>`` with a role of region, it's important to use the ``aria-label`` attribute with a clear and distinct value to differentiate between them. ::

---------------------------------------------------------------------
Example of how to add descriptive labels to HTML5 structural elements
---------------------------------------------------------------------

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

------------------
Use with *CAUTION*
------------------

* ``role="presentation"`` strips away all of the semantics from a native element.
* ``role="application"`` on an element will pass all keystrokes to the browser for handling by scripts. This disables all of the keyboard shortcuts provided by the screen reader and is only designed to be used by authors who plan on providing support for all of the application's functions via the keyboard as well as the roles, states and properties for all of its child elements.
* ``aria-hidden="true"`` will remove an element from the Accessibility API, making it invisible to a user of assistive technology. 

*Protip:* for elements intended to be hidden from all users, setting the CSS property ``display: none;`` is sufficient. It is unnecessary to also set ``aria-hidden="true"``. Once the content is revealed by changing the display property, it is too easy to forget to toggle the value of ``aria-hidden``.

*Protip:* There are legitimate use cases for ``aria-hidden`` i.e. when using an icon font that has accessible text immediately adjacent to it. Icon fonts can be focused on by certain screen readers and will remain silent upon focus. This can lead screen reader users to suspect they are missing important content. Some screen readers display what is being spoken on the screen, which helps users with certain cognitive disabilities. Icon fonts will often be rendered as a nondescript glyph in these cases. It is useful to remove them with ``aria-hidden``. It can also be used to prevent exposing a screen reader user to redundant information when an information is available in an accessible format as well as a less than accessible format.

Don't forget to manage focus on pop-ups
***************************************

Whenever a control inserts interactive content into the DOM or reveals previously hidden content (pop-up menus or modal dialog boxes), you must move focus to the container. While within the menu or dialog box, keyboard focus should remain trapped within its bounds. Hitting the ESC key or activating the "Save" or "Cancel" buttons in the dialog should close and exit the region and return focus to the element that triggered it. ``<div>`` and other container elements are not natively focusable. If you want to be able to move focus to the container it must have a ``tabindex="-1"`` attribute. It should also have an ``aria-label`` or ``aria-labelledby`` attribute defined that identifies the purpose of the dialog.

Inform users when content changes dynamically
*********************************************

If a user action or script updates the content of a page dynamically adding the ``aria-live="polite"`` attribute to the parent element of the region that changes will cause the contents of the element to be read to a screen reader user even though the element does not currently have focus. This is not intended to be used when the region contains interactive elements. 

Techniques for hiding and exposing content to targeted audiences
****************************************************************

Content that enhances the experience for one audience may be confusing or encumber a different audience. For instance, a close button that looks like ``X`` will be read by a screen reader as the letter X, unless you hide it from the Accessibility API. To visibly hide content that should be read by screen readers, edX makes a CSS ``class="sr"`` available to expose content only to screen reader users: 
::
	<a href="#">
		<span aria-hidden="true">X</span>
		<span class="sr">Close</span>
	</a>
	
In the example above, a sighted user will only see the X. A screen reader user will only hear "Close."
	
Do not add content using CSS
****************************

CSS generated content can cause many accessibility problems. Since many screen readers interact with the DOM, they are not exposed to content generated by CSS, which does not live in the DOM. There is currently no mechanism for adding alternative content for images added using CSS (either background images or pseudo elements). 

Many developers think that providing screen reader only text can be used to solve this. However, images added using this technique will not be rendered to users who have high contrast mode enabled on their operating systems. These users are likely not using screen readers, so they cannot access the visible icon, or the screen reader text.

* When adding images that represent important navigational or information elements, use ``<img>`` elements with appropriate ``alt`` attributes.  
* Content injected into the DOM using javascript is more accessible than content added using CSS.

Include a descriptive ``title`` attribute for all ``<iframe>`` elements
***********************************************************************

Use the ``title`` attribute to provide a description of the embedded content to help users decide if they would like to interact with this content or not. ``<iframe>`` titles may be presented out of context (like in a list within a dialog box), so choose text that will make sense when exposed out of context.

Make sure all links and interactive controls have labels that make sense out of context
***************************************************************************************

Screen reader users have the option of listing and navigating links and form controls out of the context of the page. When a page contains vague and non-unique text like "Click here" or "More" the purpose of these links is not clear without the text that is adjacent to them.

Choose colors that meet WCAG 2.0's minimum contrast ratios
**********************************************************

A minimum contrast between foreground and background colors is critical for users with impaired vision. You can `check color contrast ratios <https://leaverou.github.io/contrast-ratio/>`_ using any number of tools available for free online.

Testing and self-assessment
***************************

While the only way to determine if your feature is fully accessible is to manually test it with assistive technology, there are a number of automated tools you can use to perform a self assessment. Automated tools may report false positives and may not catch every possible error. However, they are a quick and easy way to avoid the most common mistakes:

* `WAVE Accessibility Toolbar <http://wave.webaim.org/toolbar/>`_ (Chrome/Firefox)
* `Web Developer Toolbar <https://addons.mozilla.org/en-US/firefox/addon/web-developer/>`_ (Firefox)
* `Chrome Accessibility Developer Tools <https://chrome.google.com/webstore/detail/accessibility-developer-t/fpkknkljclfencbdbgkenhalefipecmb>`_ 
* Your keyboard

If you want to test your feature using a screen reader, the following options are available for free:

* Voiceover (Command + F5 on Mac)
* `ChromeVox <http://www.chromevox.com>`_ (Screen reader for Chrome)
* `NVDA <http://www.nvaccess.org/download/>`_ (Screen Reader for Windows - FOSS)
* `JAWS <http://www.freedomscientific.com/Downloads/ProductDemos>`_ (Screen Reader for Windows - Commercial but free to use in 40 minute demo mode)
