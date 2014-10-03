.. _Full Screen Image:

######################
Full Screen Image Tool
######################

Some large images are difficult for students to view in the courseware.  The full screen image tool allows students to enlarge the image, so they can see all the detail in context.

****************************************
The Student View of a Full Screen Image
****************************************

The student sees the full screen image in a unit page. When the student hovers the mouse pointer over the image, the **Fullscreen** button appears:

.. image:: /Images/image-modal.png
 :alt: Image of the full screen image tool with the Full Screen button.

When the student clicks **Fullscreen**, the image opens and expands in the full browser window.  The buttons **Close**, **Zoom In**, and **Zoom Out** appear:

.. image:: /Images/image-modal-window.png
 :alt: Image of the Image Modal tool with the Full Screen button.

The student can then zoom in on the image, and drag the image to view the desired part of it:

.. image:: /Images/image-modeal-zoomed.png
 :alt: Image of the Image Modal tool with the Full Screen button.

******************************
Create a Full Screen Image
******************************

#. Upload your image file to the **Files & Uploads** page. For more information about how to do this, see :ref:`Add Files to a Course`.

#. Under **Add New Component**, click **html**, and then click **Full Screen Image**.

#. In the new component that appears, click **Edit**.

#. In the component editor, replace the default title, remove the instructional paragraph, and add text as needed.

#. Switch to the **HTML** tab.

#. Replace the following placeholders with your own content.

   * Replace the value of the <a> element's href attribute with the path to your image. Do not change the value of the class attribute. For example:

     **<a href="/static/Image1.jpg" class="modal-content">**

   * Replace the value of the <img> element's src attribute with the path to your image. For example:
     
     **<img alt="Full screen image" src="/static/Image1.jpg"/>**

   * Ensure that the value of the href and src attributes are the same, and that you do not change the class attribute. Your sample code should look like the following:

   .. code-block:: xml

     <h2>Sample Image Modal</h2>
     <a href="/static/Image1.jpg" class="modal-content">
     <img alt="Full screen image" src="/static/Image1.jpg"/>
     </a>

   .. note:: You can use this same HTML code in any HTML component, not just those components you created as full screen images.

#. Click **Save** to save the HTML component.