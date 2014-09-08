.. _LTI Component:

###############
LTI Component
###############

You may have discovered or developed an external learning application
that you want to add to your online course. Or, you may have a digital
copy of your textbook that uses a format other than PDF. You can add
external learning applications or textbooks to Studio by using a
Learning Tools Interoperability (LTI) component. The LTI component is
based on the `IMS Global Learning Tools
Interoperability <http://www.imsglobal.org/LTI/v1p1p1/ltiIMGv1p1p1.html>`_
version 1.1.1 specifications.

You can use an LTI component in several ways.

* You can add external LTI content that is displayed only, such as textbook
  content that doesn’t require a student response.

* You can add external LTI content that requires a student response. An external
  provider will grade student responses.

* You can use the component as a placeholder for syncing with an external
  grading system.

For example, the following LTI component incorporates a Cerego tool that students interact with. 

.. image:: /Images/LTIExample.png
   :alt: Cerego LTI component example

.. _LTI Information:

************************
Obtain LTI Information
************************

Before you create an LTI component from an external LTI provider in a
unit, you need the following information.

-  The **launch URL** (if the LTI component requires a student response
   that will be graded). You obtain the launch URL from the LTI
   provider. The launch URL is the URL that Studio sends to the external
   LTI provider so that the provider can send back students’ grades.

- The **LTI Passports** policy key. This policy key has three parts: an LTI ID,
  a client key, and a client secret.

  -  The **LTI ID**. This is a value that you create to refer to the external LTI
     provider. You should create an LTI ID that you can remember easily.

     The LTI ID can contain uppercase and lowercase alphanumeric
     characters, as well as underscore characters (_). It can be any length. For example, you may create an LTI ID that is
     as simple as **test_lti_id**, or your LTI ID may be a string of
     numbers and letters such as  **id_21441** or
     **book_lti_provider_from_new_york**.
  -  The **client key**. This value is a sequence of characters that you
     obtain from the LTI provider. The client key is used for
     authentication and can contain any number of characters. For example,
     your client key may be **b289378-f88d-2929-ctools.school.edu**.
  -  The **client secret**. This value is a sequence of characters that
     you obtain from the LTI provider. The client secret is used for
     authentication and can contain any number of characters. For example,
     your client secret can be something as simple as **secret**, or it
     may be a string of numbers and letters such as **23746387264** or
     **yt4984yr8**.

  To create the **LTI Passports** policy key, combine the LTI ID, client key, and client secret in the following format (make sure to include the colons):

  ``lti_id:client_key:client_secret``

  For example, an **LTI Passports** policy key may resemble any of the following:

  ``test_lti_id:b289378-f88d-2929-ctools.school.edu:secret``
  
  ``id_21441:b289378-f88d-2929-ctools.school.edu:23746387264``

  ``book_lti_provider_from_new_york:b289378-f88d-2929-ctools.company.com:yt4984yr8``

************************
Create an LTI Component
************************

Creating an LTI component in your course has three steps.

#. Add LTI to the **Advanced Module List**  policy key.
#. Register the LTI provider.
#. Create the LTI component in an individual unit.

======================================================
Step 1. Add LTI to the Advanced Module List Policy Key
======================================================

#. On the **Settings** menu, click **Advanced Settings**.

#. In the field for the **Advanced Module List** policy key, place your cursor
   between the brackets.

#. Enter ``“lti”``. Make sure to include the quotation marks, but not the
   period.

   .. image:: /Images/LTIPolicyKey.png
     :width: 500
     :alt: Image of the advanced_modules key in the Advanced Settings page, with the LTI value added

.. note:: If the **Advanced Module List** field already contains text, place your cursor directly
   after the closing quotation mark for the final item, and then enter a comma
   followed by ``“lti”`` (make sure that you include the quotation marks).

4. At the bottom of the page, click **Save Changes**.

The page refreshes automatically. At the top of the page,
you see a notification that your changes have been saved.

==========================================
Step 2. Register the External LTI Provider
==========================================

To register the external LTI provider, you’ll add the **LTI Passports** policy
key to the course's advanced settings.

#. On the **Advanced Settings** page, locate the **LTI Passports**
   policy key.

#. Place your cursor between the brackets.

#. Enter the **LTI Passports** policy key surrounded by quotation marks.

   For example, the text in the **LTI Passports** field may resemble the following.

   ``"test_lti_id:b289378-f88d-2929-ctools.umich.edu:secret"``

   If you have multiple LTI providers, separate the values for each **LTI
   Passports** policy key with a comma. Make sure to surround each entry with
   quotation marks.

   .. code-block:: xml

      "test_lti_id:b289378-f88d-2929-ctools.umich.edu:secret",
      "id_21441:b289378-f88d-2929-ctools.school.edu:23746387264",
      "book_lti_provider_from_new_york:b289378-f88d-2929-ctools.company.com:yt4984yr8"

4. At the bottom of the page, click **Save Changes**.

The page refreshes automatically. At the top of the page, you see a
notification that your changes have been saved, and you can see your entries
for the **LTI Passports** policy key.

==========================================
Step 3. Add the LTI Component to a Unit
==========================================

#. In the unit where you want to create the problem, click **Advanced**
   under **Add New Component**, and then click **LTI**.
#. In the component that appears, click **Edit**.
#. In the component editor, specify the settings that you want. See :ref:`LTI Component Settings` for a description of each setting.
#. Click **Save**.

.. _LTI Component settings:

**********************
LTI Component Settings
**********************

.. list-table::
   :widths: 10 80
   :header-rows: 1

   * - Setting
     - Description
   * - Custom Parameters
     - Enables you to add one or more custom parameters. For example, if you've added an e-book, you can set a custom parameter that opens the e-book to a specific page. You could also use a custom parameter to set the background color of the LTI component.

       Every custom parameter has a key and a value. You must add the key and value in the following format.

       ::

          key=value

       For example, a custom parameter may resemble the following.

       ::

          bgcolor=red

          page=144

       To add a custom parameter, click **Add**.
   * - Display Name
     - Specifies the name of the problem. This name appears above the problem and in the course ribbon at the top of the page in the courseware. Analytics reports may also use the display name to identify this component.
   * - Hide External Tool
     - Indicates whether you want to launch an external tool or to use this component as a placeholder for syncing with an external grading system. If you set the value to **True**, Studio hides the **Launch** button and any IFrames for this component. By default, this value is set to **False**.
   * - LTI ID
     - Specifies the LTI ID for the external LTI provider. This value must be the same LTI ID that you entered on the **Advanced Settings** page.
   * - LTI URL
     - Specifies the URL of the external tool that this component launches. This setting is applicable when **Hide External Tool** is set to False.
   * - Open in New Page
     - Indicates whether the problem opens in a new page. If you set this value to **True**,          the student clicks a link that opens the LTI content in a new window. If you set this value to **False**, the LTI content opens in an IFrame in the current page. This setting is applicable when **Hide External Tool** is set to False.
   * - Scored
     - Indicates whether the LTI component receives a numerical score from the external LTI system. By default, this value is set to **False**.
   * - Weight
     - Specifies the number of points possible for the problem. By default, if an external LTI provider grades the problem, the problem is worth 1 point, and a student’s score can be any value between 0 and 1. This setting is applicable when **Scored** is set to **True**.

       For more information about problem weights and computing point scores, see :ref:`Problem Weight`.
