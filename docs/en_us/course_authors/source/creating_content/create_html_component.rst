.. _Working with HTML Components:


#############################
Working with HTML Components
#############################

***********************
HTML Component Overview
***********************

HTML, or HyperText Markup Language, is the standard markup language used to
create web pages. Web browsers present HTML code in a more readable format.

When students see text and images in your course, they are seeing HTML code
that is formatted and presented by their browsers. For more information about
HTML, see `Wikipedia <http://en.wikipedia.org/wiki/HTML>`_.

HTML components are the basic building blocks of your course content. You use
HTML components to add and format text, links, images, and more. You can choose
to create HTML components directly in HTML code, or using a Visual editor that
hides the HTML code details, as described below.

For more information, see the following topics:

* :ref:`Options for Editing HTML Components`
* :ref:`The Visual Editor`
* :ref:`The Raw HTML Editor`
* :ref:`HTML Component Templates`
* :ref:`Create an HTML Component`
* :ref:`Add a Link in an HTML Component`
* :ref:`Add an Image to an HTML Component`
* :ref:`Import LaTeX Code`

.. note:: 
 Review :ref:`Developing Your Course Index` and :ref:`Best Practices for HTML
 Markup` before you start working with HTML components.

To add an instant hangout to an HTML component, see :ref:`Google Instant
Hangout`.


.. _Options for Editing HTML Components:

********************************************
Options for Editing HTML Components
********************************************

You can work with HTML in two ways:

* :ref:`The Visual Editor`
  
  With the Visual editor you can create, edit, and format content in a word
  processing-like interface, without using HTML code directly. With the Visual
  editor, you can more easily format your content, and add links and images. The
  Visual editor provides access to HTML code so you can make small changes to
  formatting, if required. However, the HTML view in the Visual editor does not
  provide the detailed control you can get with the Raw HTML editor, and does
  not support custom formatting or scripts.

* :ref:`The Raw HTML Editor`

  With the Raw HTML Editor, you work directly with HTML code. If you need to use
  custom formatting or scripts in your content, you should use the Raw HTML
  Editor.


Set the Editor for an HTML Component
************************************

You set the editor for an HTML component in the **Settings** tab:

.. image:: ../Images/set_html_editor.png
 :alt: The Editor selection drop-down list in the HTML Component Settings tab

Select **Visual** or **Raw**. When you change the editor, you must click
**Save** and re-open the component to begin using the new editor.

.. warning:: 
 If you work with content in the Raw HTML editor, then switch to the Visual
 editor, you may lose custom HTML that you created. Therefore, it is recommended
 that you start by using the Visual editor, then switch to the Raw HTML editor
 when you need to create custom HTML.

.. _The Visual Editor:

*****************************************
The Visual Editor
*****************************************

The Visual editor provides a “what you see is what you get” (WYSIWYG) interface
that allows you to format text by clicking the formatting buttons at the top of
the editor.

.. image:: ../Images/HTMLEditor.png
 :alt: Image of the HTML component editor

The following image shows call-outs for the editing options and is followed by
descriptions.

.. image:: ../Images/HTML_VisualView_Toolbar.png
  :alt: Image of the HTML editor, with call-outs for formatting buttons

#. Choose a formatting style for the selected paragraph, such as heading 1,
   heading 2, or paragraph.
#. Choose a font family for selected text, such as Arial, Courier New, or Times
   New Roman.
#. Format selected text in bold.
#. Format selected text in italics.
#. Underline selected text.
#. Apply a color to the selected text.
#. Format selected text as code.
#. Create a bulleted list.
#. Create a numbered list.
#. Decrease and increased the indentation of the selected paragraph.
#. Format the selected paragraph as a blockquote.
#. Create a link from the selected text. See :ref:`Add a Link in an HTML
   Component`.
#. Delete the current link.
#. Insert an image at the cursor. See :ref:`Add an Image to an HTML Component`.
#. Work with HTML source code, described below.


.. _Work with HTML code:


Work with HTML code in the Visual editor
*****************************************

To work with HTML source code for the content you create in the Visual editor,
click **HTML**  in the editor toolbar. The HTML source code editor opens:

.. image:: ../Images/HTML_source_code.png
 :alt: Image of the HTML source code editor

Edit the HTML code as needed. 

You should not add custom styles or scripts in the HTML code view in the
Visual editor. Use the Raw HTML editor instead.

Click **OK** to close the source code editor and apply your changes in the
Visual editor. The Visual editor then attempts to ensure the underlying HTML
code is valid; for example, if you do not close a paragraph tag, the editor will
close it for you.

.. warning:: 
 Clicking **OK** in the source code editor does not save your changes to the
 HTML component.  You return to the component editor, where your changes are
 applied.  You must then also click **Save** to save your changes and close the
 component. If you click **Cancel**, the changes you made in the HTML source
 code are lost.

.. _The Raw HTML Editor:

*****************************
The Raw HTML Editor
*****************************

When you select the Raw editor for the HTML component, you edit your content in
a text editor:

.. image:: ../Images/raw_html_editor.png
 :alt: The Raw HTML editor

You must enter valid HTML. The Raw HTML editor does not validate your HTML code.
Therefore you should thoroughly test the HTML content in your course.


.. _HTML Component Templates:

*****************************
HTML Component Templates
*****************************

When you create a new HTML component, you select from a list of templates:

.. image:: ../Images/html_templates.png
 :alt: The list of HTML Component templates

The Raw HTML template is set to use the Raw HTML editor. All other templates use
the Visual editor.

For any HTML component, you can change the editor, regardless of the template
used to create the component. See `Set the Editor for an HTML Component`_.



.. _Create an HTML Component:

*****************************
Create an HTML Component
*****************************

To create an HTML component:

1. Under **Add New Component**, click **html**.

  .. image:: ../Images/NewComponent_HTML.png
   :alt: Image of adding a new HTML component

2. Select the template. 

   The rest of these instructions assume you selected
   **Text**, which creates an empty component with the Visual editor selected.

   An empty component appears at the bottom of the unit.

  .. image:: ../Images/HTMLComponent_Edit.png
   :alt: Image of an empty HTML component

3. In the component, click **Edit**.

   The HTML component opens in the Visual editor.

  .. image:: ../Images/HTMLEditor_empty.png
   :alt: Image of the HTML component editor

4. Enter and format your content. You can :ref:`Work with HTML code` if needed.

5. Enter a display name (the name that you want students to see). To do this,
   click **Settings** in the upper-right corner of the component editor, and
   then enter text in the **Display Name** field.

   To return to the text editor, click **Editor** in the upper-right corner.

6. Click **Save** to save the HTML component.

When using the Visual editor, you can also:

* :ref:`Add a Link in an HTML Component`
* :ref:`Add an Image to an HTML Component`
* :ref:`Import LaTeX Code`

.. _Add a Link in an HTML Component:

***********************************
Add a Link in an HTML Component
***********************************

When using the Visual editor, to add a link to a website, course unit, or file
in an HTML component, you work with the **Insert link** dialog box.

.. image:: ../Images/HTML_Insert-EditLink_DBox.png
 :alt: Image of the Insert link dialog box

You can:

* :ref:`Add a Link to a Website`
* :ref:`Add a Link to a Course Unit`
* :ref:`Add a Link to a File`

.. _Add a Link to a Website:

Add a Link to a Website
***********************************

To add a link to a website:

#. Select the text that you want to make into the link.

#. Click the link icon in the toolbar.

#. In the **Insert link** dialog box, enter the URL of the website that you want
   in the **URL** field.

   .. image:: ../Images/HTML_Insert-EditLink_Website.png
    :alt: Image of the Insert link dialog box

#. If you want the link to open in a new window, click the drop-down arrow next
   to the **Target** field, and then select **New Window**. If not, you can
   leave the default value.

#. Click **OK**.

#. Save the HTML component and test the link.


.. _Add a Link to a Course Unit:


Add a Link to a Course Unit
***********************************

You can add a link to a course unit in an HTML component.

#. Obtain the unit identifier of the unit you're linking to. To do this, open
   the unit page in Studio, and copy the unit ID from the **Unit Identifier**
   field under **Unit Location** in the right pane.
   
   .. image:: ../Images/UnitIdentifier.png
    :alt: Image of the unit page with the unit identifier circled

#. Open the HTML component where you want to add the link.

#. Select the text that you want to make into the link.

#. Click the link icon in the toolbar.

#. In the **Insert link** dialog box, enter the following in the **URL** field.

   ``/jump_to_id/<unit identifier>``

   Make sure to replace <unit identifier> (including the brackets) with the unit
   identifier that you copied in step 2, and make sure to include both forward slashes (/).

   .. image:: ../Images/HTML_Insert-EditLink_CourseUnit.png
    :alt: Image of the Insert link dialog box with a link to a unit identifier

#. If you want the link to open in a new window, click the drop-down arrow next
   to the **Target** field, and then select **New Window**. If not, you can
   leave the default value.

#. Click **Insert**.

#. Save the HTML component and test the link.

.. _Add a Link to a File:


Add a Link to a File
***********************************

You can add a link in an HTML component to any file you've uploaded for the
course. For more information about uploading files, see :ref:`Add Files to a
Course`.

#. On the **Files & Uploads** page, copy the **Embed URL** of the file.


  .. image:: ../Images/HTML_Link_File.png
   :alt: Image of Files and Uploads page with the URL field circled 
  
  .. note:: 
   You must use the **Embed URL** to link to the file, not the **External URL**.

2. Select the text that you want to make into the link.

#. Click the link icon in the toolbar.

#. In the **Insert link** dialog box, enter the following in the **URL** field.

   ``/static/FileName.type``

   Make sure to include both forward slashes (/).

   .. image:: ../Images/HTML_Insert-EditLink_File.png
    :alt: Image of the Insert link dialog box with a link to a file

#. If you want the link to open in a new window, click the drop-down arrow next
   to the **Target** field, and then select **New Window**. If not, you can
   leave the default value.

#. Click **Insert**.

#. Save the HTML component and test the link.

.. _Add an Image to an HTML Component:

***********************************
Add an Image to an HTML Component
***********************************

When using the Visual editor, you can add any image that you have uploaded for
the course to an HTML component. For more information about uploading images,
see :ref:`Add Files to a Course`.

.. note:: 
 Review :ref:`Best Practices for Describing Images` before you add images to
 HTML components.

To add an image, you'll need the URL of the image that you uploaded to the
course. You'll then create a link to the image in the HTML component.

#. On the **Files & Uploads** page, copy the **Embed URL** of the image that you
   want.

  .. image:: ../Images/image_link.png
   :alt: Image of the Files & Upload page with the Embed URL for the image
       circled

  .. note:: 
   You must use the **Embed URL** to add the image, not the **External URL**.

2. Click the image icon in the toolbar.

#. In the **Insert image** dialog box, enter the following in the **Source**
   field.

   ``/static/FileName.type``

   Make sure to include both forward slashes (/).

   .. image:: ../Images/HTML_Insert-Edit_Image.png
    :alt: Image of the Insert image dialog box with a reference to a file

4. Enter alternative text in the **Image description** field. This text becomes
   the value of the ``alt`` attribute in HTML and is required for your course to
   be fully accessible. See :ref:`Best Practices for Describing Images` for more
   information.

#. As needed, customize the image dimensions. Keep **Constrain proportions**
   checked to ensure the image keeps the same width and height proportions.

#. To change the spacing and border of the image, click the **Advanced** tab. 

   .. image:: ../Images/HTML_Insert-Edit_Image_Advanced.png
    :alt: Image of the Insert image dialog box Advanced tab

#. Enter the **Vertical space**, **Horizontal space**, and **Border** as needed.
   The values you enter are automatically added to the **Style** field.

#. Click **OK** to insert the image in the HTML component.

#. Save the HTML component and test the image.


.. _Import LaTeX Code:

****************************************
Import LaTeX Code into an HTML Component
****************************************

You can import LaTeX code into an HTML component. You might do this, for
example, if you want to create "beautiful math" such as the following.

.. image:: ../Images/HTML_LaTeX_LMS.png
 :alt: Image of math formulas created with LaTeX

.. warning:: 
 The LaTeX processor that Studio uses to convert LaTeX code to XML is a third-
 party tool. We recommend that you use this feature with caution. If you do use
 it, make sure to work with your Program Manager.

This feature is not enabled by default. To enable it, you have to change the
advanced settings in your course.

To create an HTML component that contains LaTeX code:

#. Enable the policy key in your course.

   #. In Studio, click **Settings**, and then click **Advanced Settings**.
   #. In the field for the **Enable LaTeX Compiler** policy key, change
      **false** to **true**.
   #. At the bottom of the page, click **Save Changes**.

#. In the unit where you want to create the component, click **html** under
   **Add New Component**, and then click **E-text Written in LaTeX**. The new
   component is added to the unit.

#. Click **Edit** to open the new component. The component editor opens.

  .. image:: ../Images/latex_component.png
   :alt: Image of the HTML component editor with the LaTeX compiler.

4. In the component editor, click **Launch Latex Source Compiler**. The LaTeX
   editor opens.

   .. image:: ../Images/HTML_LaTeXEditor.png
    :alt: Image of the HTML component editor with the LaTeX compiler

#. Write LaTeX code as needed. You can also upload a LaTeX file into the editor
   from your computer by clicking **Upload** in the bottom right corner.

#. When you have written or uploaded the LaTeX code you need, click **Save &
   Compile to edX XML** in the lower-left corner.

   The component editor closes. You can see the way your LaTeX content looks.

   .. image:: ../Images/HTML_LaTeX_CompEditor.png
    :alt: Image of the LaTeX component

#. On the unit page, click **Preview** to verify that your content looks the way
   you want it to in the LMS.

   If you see errors, go back to the unit page. Click **Edit** to open the
   component again, and then click **Launch Latex Source Compiler** in the
   lower-left corner of the component editor to edit the LaTeX code.
