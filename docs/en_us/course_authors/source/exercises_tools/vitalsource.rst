.. _VitalSource:

#########################
VitalSource E-Reader Tool
#########################

The VitalSource Bookshelf e-reader tool provides your students with easy access to electronic books. In addition to reading text, students can quickly browse and search content (including figures and notes), use multiple highlighters, create and manage notes, and copy notes into external documents.

.. image:: /Images/VitalSource.png
   :width: 500
   :alt: VitalSource e-book with highlighted note

For more information about Vital Source and its features, visit the `VitalSource Bookshelf support site <https://support.vitalsource.com>`_.

.. note:: Before you add a VitalSource Bookshelf e-reader to your course, you must work with Vital Source to make sure the content you need already exists in the Vital Source inventory. If the content is not yet available, Vital Source works with the publisher of the e-book to create an e-book that meets the VitalSource Bookshelf specifications. **This process can take up to four months.** The following steps assume that the e-book you want is already part of the Vital Source inventory.

**************************
Add a VitalSource E-Reader
**************************

Adding a VitalSource Bookshelf e-reader has several steps:

#. :ref:`Obtain specific information<VS Obtain VS Info>` about your e-book from Vital Source.

#. :ref:`Modify the course's advanced settings<VS Modify Advanced Settings>` to allow you to create a Vital Source Learning Tools Interoperability (LTI) component.

#. :ref:`Add the VitalSource Bookshelf e-reader<VS Add VS EReader>` to a unit.

.. _VS Obtain VS Info:

===========================================
Step 1. Obtain Information from VitalSource
===========================================

To create a VitalSource Bookshelf e-reader, you need the following information from Vital Source:

- The **LTI Passports** policy key. This policy key enables you to create an
  LTI component for the VitalSource Bookshelf e-reader. For more information
  about the **LTI Passports** policy key, see :ref:`LTI Information` in
  :ref:`LTI Component`.

- The Vital Souce Book ID (VBID) for your e-book. This is a specific code that Vital Source creates for the book when Vital Source adds the e-book to its inventory.

To obtain this information, your course team selects a member point person
(MPP) to work with Vital Source. Vital Source delivers the **LTI Passports**
policy key and VBID to the MPP.


.. _VS Modify Advanced Settings:

=============================================
Step 1. Modify the Course's Advanced Settings
=============================================

In this step, you'll modify the course's advanced settings to allow you to
create an LTI component and add the **LTI Passports** policy key for Vital
Source.

#. In Studio, click the **Settings** menu, and then click **Advanced Settings**.

#. In the field for the  **Advanced Module List** policy key, place your cursor
   between the brackets.

#. Enter ``“lti”``. Make sure to include the quotation marks, but not the
   period.

   .. image:: /Images/LTIPolicyKey.png
    :alt: Image of the Advanced Module List key in the Advanced Settings page, with the LTI value added

  .. note:: If the value field already contains text, place your cursor directly after the closing quotation mark for the final item, and then enter a comma followed by ``“lti”`` (make sure that you include the quotation marks). For example, the value for **Advanced Module List** may resemble the following:

   ``["value_1","lti"]``

4. Scroll down to the **LTI Passports** policy key.

#. In the policy value field, place your cursor between the brackets, and then
   enter the value for the **LTI Passports** policy key that you obtained from
   Vital Source. Make sure to surround the value with quotation marks.

   For example, the value in this field may resemble the following:

   ``"id_21441:b289378-ctools.school.edu:23746387264"``

6. At the bottom of the page, click **Save Changes**.

The page refreshes automatically. At the top of the page, you see a notification that your changes have been saved.

.. _VS Add VS EReader:

==============================================================
Step 3. Add the VitalSource Bookshelf E-Reader to a Unit
==============================================================

To add the VitalSource Bookshelf e-reader to a unit, you'll create an LTI component, and then configure several settings in the component.

#. In the unit where you want to create the problem, click **Advanced** under **Add New Component**, and then click **LTI**.

#. In the component that appears, click **Edit**.

#. In the **Display Name** field, type the name of your e-book. This name appears at the top of the component and in the course ribbon at the top of the page in the courseware.

#. Next to **Custom Parameters**, click **Add**.

#. In the field that appears, enter the following (where ``VitalSourceCode`` is the VBID for the e-book):

   ``vbid=VitalSourceCode``

   If you want to experiment with an e-book in your course, but you don't yet have a VBID for your e-book, you can enter ``vbid=L-999-70103`` to create a link to *Pride and Prejudice*.

#. If you want your e-book to open to a specific page, click **Add** next to **Custom Parameters** again, and then add the following (where ``35`` is the page of the e-book):

   ``book_location=page/35``

#. In the **Launch URL** field, enter the following (make sure to use ``https`` instead of ``http``):

  ``https://bc.vitalsource.com/books/book``

8. In the **LTI ID** field, enter the following:

  ``vital_source``

9. Click **Save**.

**************************
Information for Students
**************************

Each institution's Vital Source account manager will train the MPP on the VitalSource Bookshelf e-reader and provide supporting documentation as part of the onboarding process. However, to improve the learner experience, we recommend that you provide the following explanation of the e-reader to your students:

  Digital textbooks in the VitalSource Bookshelf e-reader offer simple, user-friendly navigation and instant, intuitive access to content. You'll most often use several VitalSource Bookshelf e-reader features during the course:

  * Browse content, figures, and notes and filter search results.
  * Use multiple highlighters.
  * Create and manage notes.
  * Copy and paste notes into external documents.

  For more information about how to use these features, visit the `VitalSource Bookshelf support site <https://support.vitalsource.com>`_.

