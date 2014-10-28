.. _Wikis:

############################
Wikis
############################

Wikis allow students to share and edit notes about course material between each
other. You can seed a wiki with a skeleton of your course materials from your
syllabus, or provide supporting material for students to review and edit. Wikis can
help students collaboratively react to material being presented.  Depending on
your course, you may like to use the wiki a lot or not at all.

* :ref:`Overview_wikis`

* :ref:`Organizing_wikis`

* :ref:`Moderating_wikis`

* :ref:`Running_wikis`

* :ref:`Hiding_wikis`

.. _Overview_wikis:

********************************
Overview
********************************

Both students and staff can use wiki pages to create a growing repository of
information about a course. The wiki utilizes a markup language that allows for easy
formatting, embedding of images, and linking. It differs from discussions in
that content, not contributors, are emphasized.

Course staff and students can edit the content of a wiki by default. Staff can
lock pages of their choosing.

.. _Organizing_wikis:

********************************
Setting up your wiki
********************************

Wikis adopt a hierarchical folder structure. A course's wiki can be greatly improved if
you are able to include a page for each lesson. Those pages can be blank, or
can include instructor or student notes for that lesson.

.. _Running_wikis:

############################
Running
############################

All pages in edX wikis use Markdown syntax. This allows for quick and simple
formatting, such as the following examples::
  HEADERS

  #     Header 1
  ##    Header 2
  ###   Header 3
  ####  Header 4
  ##### Header 5
  
  HORIZONTAL RULES
  
  ---
  
  LINKING TO PAGES
  
  [Link to external page](http://www.edx.org)
  [Link to internal wiki page](test_page)
  
  CODE BLOCKS
  
  ```python
  def foo(bar):
    print bar

  foo('baz')
  ```
A more complete reference is available on 
http://daringfireball.net/projects/markdown/

.. _Moderating_wikis:

********************************
Moderating
********************************

As a staff member for a course, you are able to be lock wiki pages and revert
changes on a wiki page.

============================================
Locking a wiki page
============================================

.. image:: ../Images/wiki_locking.png 
 :alt: The locking options in the wiki settings page

============================================
Reverting a wiki page
============================================

.. image:: ../Images/wiki_reversion.png 
 :alt: Image of the wiki revision page

.. _Hiding_wikis:
..
.. ********************************
.. Hiding
.. ********************************
..
.. To hide a wiki in XML authoring, remove the `{"type": "wiki"}` entry in
.. your `/policies/TERM/policy.json` file.
