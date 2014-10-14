.. _Google Instant Hangout:

###########################################
Google Instant Hangout Tool
###########################################

This chapter describes how you can use instant hangouts in your course. See:

* :ref:`Hangouts_Overview`
* :ref:`Instant Hangouts in Your Course`
* :ref:`The Student Experience`
* :ref:`Limitations`
* :ref:`Create the Instant Hangout`

.. _Hangouts_Overview:

*****************
Overview
*****************

You can add the ability for students to participate in instant hangouts directly from your course.

With instant hangouts, students can:

* Interact through live video and voice.
* Share screens and watch videos together.
* Collaborate on documents.

For a full list of instant hangout features, see the `Google Hangouts page <http://www.google.com/+/learnmore/hangouts/>`_.

.. note:: Students who want to participate in instant hangouts must have a Google account.  You should note this in your course materials.

.. _Instant Hangouts in Your Course:

**********************************
Instant Hangouts in Your Course
**********************************

You can add one or more instant hangouts in your course. For example, you can add an instant hangout:

* In a page, to provide students with a hangout for the entire course. See :ref:`Adding Pages to a Course` for more information.

* In an HTML component, to provide a hangout for students working on that specific course unit. See :ref:`Working with HTML Components` for more information about creating HTML components.

An instant hangout is specific to the page it is opened from. For example, students who join a hangout from one course unit interact among themselves, while students who join a hangout from another unit interact in a different hangout.

.. _The Student Experience:

*************************
The Student Experience
*************************

When you add the instant hangout to your course, a control for the hangout appears on that page. The following example shows the control in a course unit. The control shows that the student can start the hangout and be the first participant.

.. image:: /Images/hangout_unit.png
 :alt: Image of the instant hangout control on a unit

To start the hangout, the student clicks **Start the Hangout**. (After the first student clicks **Start the Hangout**, other students see a **Join the Hangout** button.)

The following example shows the control in a page when a hangout has already started. The control has a **Join the Hangout** button, and shows that one other student is already in the hangout.

.. image:: /Images/hangout_static_page.png
 :alt: Image of the instant hangout control on a page

To join the hangout, the student clicks **Join the Hangout**.

If not already logged in, the student is prompted to log in to Google:

.. image:: /Images/google_login.png
 :alt: Image of the Google login page

Students who do not have a Google account can create one from the login page.

After the student has logged in to Google, the hangout opens in a separate browser window:

.. image:: /Images/GoogleHangout_WithPeople.png
 :alt: Image of the instant hangout

.. _Limitations:

****************
Limitations
****************

Currently, only ten students can join a single instant hangout. You should note this in your course materials.

Students in hangouts that are started from different pages in your course are counted separately. So you can have ten students participating in a hangout started from one unit, and ten other students in a hangout started from a different unit.

.. _Create the Instant Hangout:

**************************************************
Create the Instant Hangout
**************************************************

To create an instant hangout in your course:

#. Get the `instant hangout JavaScript file from GitHub <https://raw.github.com/google/instant-hangouts/master/instanthangouts-0.1.0.js>`_.

#. Copy the text of this file into a text editor on your computer, and save the file as a JavaScript file (that is, when you save the file, change the extension from .txt to .js).

   .. note::  Make sure that you copy the raw GitHub file, which does not contain formatting. Do not copy the formatted file. Any formatting will cause the JavaScript to not work correctly.

#. Upload the JavaScript file to the **Files & Uploads** page in your course. See :ref:`Add Files to a Course` for more information.

#. In either a page or an HTML component, open the HTML editor.

#. On the first line, add the JavaScript file you uploaded in a <script> tag. For example, if your JavaScript file is named **instanthangouts-0.1.0.js**, you would enter the following::
  
    <script src='/static/instanthangouts-0.1.0.js'/>

#. After the <script> tag, add::
  
    <div class='instanthangouts'/>

#. Add any additional text and tags that you want.

   For example, the complete HTML could be::

    <p>Join an instant hangout by clicking the button below. 
    You can use the hangout to have live video discussions with other students.</p>
    <script src='/static/instanthangouts-0.1.0.js'></script>
    <div class='instanthangouts'/>

#. Test the instant hangout in your course.

=============================
Updating the JavaScript File
=============================

Google will periodically update the instant hangouts JavaScript file.  To receive update notifications, go to the `instant hangouts repository page <https://github.com/google/instant-hangouts/>`_, and then click **Watch** in the upper-right area of the page. 

To use an updated JavaScript file in your course, we recommend that you copy the JavaScript from the repository into a file that has the same name as the file that you uploaded to your course. When you upload the new file, the new file replaces the previous file.

.. warning:: If you include version numbers in the file names of uploaded files, you will have to edit any HTML components or pages that include an instant hangout control every time that you update the JavaScript file.
