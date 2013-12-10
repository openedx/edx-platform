.. _Working with LTI Components:

Working with LTI Components
============================

Overview
---------

You may have a digital copy of your textbook that uses a format other than PDF. If so, you
can add that textbook to Studio by using a Learning Tools Interoperability (LTI) XModule (**SP: OK 
to say "component" instead of "XModule"? Our docs haven't talked about 
XModules yet, so users may not know what they are.**).
The LTI XModule is based on the 
`IMS Global Learning Tools Interoperability <http://www.imsglobal.org/LTI/v1p1p1/ltiIMGv1p1p1.html>`_ 
version 1.1.1 specifications.

You can use an LTI component in two ways.

- You can show external LTI content. This content is displayed only.
- You can show LTI content that will be graded by an external provider.

Before you create an LTI component from an external LTI provider in a unit, you must
have the following information so that you can register that provider.

- The **LTI ID**. This value is an internal string that specifies the external LTI 
  provider that you want to add to the course. (**SP: How does the user obtain this ID? 
  Does it have to be a certain length?**)
  
  The LTI ID can contain uppercase and lowercase alphanumeric characters, 
  as well as underscore characters (_). For example, your LTI ID may be (**SP: Need
  example**). 

- The **client key**. This value is a string that is used for OAuth authentication. 
  You can obtain this value from the external LTI provider. (**SP: What is OAuth
  authentication? Do end users need to know what it is, or can we just say "that
  Studio uses to verify that the LTI provider is safe" [or similar]? Does the key have to
  have a specific number of characters? Are all types of characters allowed?**) For 
  example, your client key may be (**SP: Need example**).

- The **client secret**. This value is a string that is used for OAuth authentication. 
  You can obtain this value from the external LTI provider. (**Does the key have to
  have a specific number of characters? Are all types of characters allowed?** For 
  example, your client key may be (**SP: Need example**).


Create an LTI Component
-----------------------

Creating an LTI component in your course has three steps.
 
#. Add LTI to the **advanced_modules** policy key. 
#. Register the LTI provider.
#. Create the LTI component in an individual unit.

Add LTI to the Advanced Modules Policy Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#. On the **Settings** menu, click **Advanced Settings**.

#. On the **Advanced Settings** page, locate the **Manual Policy
   Definition** section, and then locate the **advanced_modules**
   policy key (this key is at the top of the list).

   .. image:: Images/AdvancedModulesEmpty.gif

#. Under **Policy Value**, place your cursor between the brackets, and
   then enter **"lti"**. Make sure to include the quotation marks, 
   but not the period.
   
   .. image:: Images/LTI_Policy_Key.gif

   **Note** *If the **Policy Value** field already contains text, place your cursor directly after the
   closing quotation mark for the final item, and then enter a comma followed by **"lti"** (make sure that you 
   include the quotation marks).*

#. At the bottom of the page, click **Save Changes**.

   The page refreshes automatically. At the top of the page, you see a
   notification that your changes have been saved.

Register the External LTI Provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To regiser the external LTI provider, you'll add the LIT ID, the client key, and 
the client secret in the **lti_passports** policy key.

#. On the **Advanced Settings** page, locate the **lti_passports**
   policy key.

#. Under **Policy Value**, place your cursor between the brackets, and
   then enter the LTI ID, client key, and client secret in the following format. 

   "{lti_id}:{client_key}:{client_secret}"
   
   For example, the value in the lti_passports field may be the following.
   
   "(**SP: Need an example.**)"
   
   If you have multiple LTI providers, separate the values with a comma.

   ::
        
   "{lti_id_1}:{client_key_1}:{client_secret_1}",
   "{lti_id_2}:{client_key_2}:{client_secret_2}",
   "{lti_id_3}:{client_key_3}:{client_secret_3}"

#. At the bottom of the page, click **Save Changes**.

   The page refreshes automatically. At the top of the page, you see a
   notification that your changes have been saved.

Add the LTI Component to a Unit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. In the unit where you want to create the problem, click **Advanced**
   under **Add New Component**.
#. In the list of problem types, click **LTI**.
#. In the component that appears, click **Edit**.
#. In the component editor, set the options that you want.
#. Click **Save**.

(**SP: It would be great to clean up the text of the UI for this component. I'm happy
to suggest text.**)

.. list-table::
   :widths: 10 80
   :header-rows: 1

* - **Display Name**
  - Specifies the name of the problem.

* - **custom_parameters** [string] 
  - With the "+ Add" button, multiple custom parameters can be
    added. Basically, each individual external LTI provider can have a separate
    format custom parameters. For example::

        key=value
        
    (**SP: I'm not clear on what these are. What would a custom parameter be used for? 
    Can we provide a specific example?**)

* - **graded** 
  - Indicates whether the grade for the problem counts towards student's total grade. By
    default, this value is set to **False**.

* - **has_score**
  - Specifies whether the problem has a numerical score. By default, this value 
    is set to **False**.

* - **launch_url**
  - Lists the URL that Studio sends to the external LTI provider so that the provider
    can send back students' grades. This setting is only used if **graded** is set to 
    **True**.

* - **lti_id** 
  - Specifies the LTI ID for the external LTI provider. This value must be one of the
    LTI IDs that you entered on the **Advanced Settings** page.

* - **open_in_a_new_page** [boolean]
  - Indicates whether the problem opens in a new page. If you set this value to True, 
    the student clicks a link that opens the LTI content in a new window. If you set
    this value to False, the LTI content opens in an IFrame in the current page.

* - **weight** [float]
  - If the problem will be graded by an external LTI provider,
    the raw grade will be in the range [0.0, 1.0]. In order to change this range,
    set the `weight`. The grade that will be stored is calculated by the formula:

        stored_grade = raw_grade * weight

    (**SP: Raw grade means points earned?**)
