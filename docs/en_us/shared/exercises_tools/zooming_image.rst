.. _Zooming Image:

##################
Zooming Image Tool
##################

You may want to present information to your students as an image. If your image is very large or very detailed, students may not be able to see all the information in the image. You can use the zooming image tool to enlarge areas of your image as the student moves the mouse over the image, as in the example below.

.. image:: /Images/Zooming_Image.png
  :alt: Example zooming image tool showing a chemistry exercise

***********************************
Components of a Zooming Image Tool
***********************************

To create a zooming image tool, you need the following files.

* The image that you want students to see when they access the unit.
* The image that appears in the magnified area when a student clicks the regular image. This image may be larger than the regular image.
* The **jquery.loupeAndLightbox.js** JavaScript file. Every zooming image tool uses this JavaScript file, and you won't make any changes to it. `To download this file, right-click here <http://files.edx.org/jquery.loupeAndLightbox.js>`_, and then click **Save Link As** to save the file on your computer.

****************************
Create a Zooming Image Tool
****************************

#. Upload your regular-sized image file, your small image file, and the **jquery.loupeAndLightbox.js** file to the **Files & Uploads** page. For more information about how to do this, see :ref:`Add Files to a Course`.

#. Under **Add New Component**, click **html**, and then click **Zooming Image**.

#. In the new component that appears, click **Edit**.

#. In the component editor, replace the default problem text with your own text.

#. Switch to the **HTML** tab.

#. Replace the following placeholders with your own content.

   - Replace the following file name and path with the name and path of the image that you want to appear magnified when the user hovers over the regular image.

     **https://studio.edx.org/c4x/edX/DemoX/asset/pathways_detail_01.png**

     For example, your file name and path may be **/static/Image1.jpg**.

   - Replace the following file name and path with the name and path of the image that you want to appear when the page opens.
     
     **https://studio.edx.org/c4x/edX/DemoX/asset/pathways_overview_01.png**

     For example, your file name and path may be **/static/Image2.jpg**.

   - Replace the following name and file path with the name and path of the JavaScript file for your course.

     **https://studio.edx.org/c4x/edX/DemoX/asset/jquery.loupeAndLightbox.js**

     Because you uploaded the **jquery.loupeAndLightbox.js** file to the **Files & Uploads** page, your file name and path is **/static/jquery.loupeAndLightbox.js**.

   - (Optional) If you want the magnified area to be larger or smaller, change the **width** and **height** values from 350 to larger or smaller numbers. For example, you can change both numbers to 450. Or, if you want a horizontal oval instead of a circle, you can change the **width** value to a number such as 500 and the **height** value to a number such as 150.

   The HTML in your zooming image tool may resemble the following.

   .. image:: /Images/ZoomingImage_Modified.png
     :alt: Example HTML for a zooming image tool

#. Click **Save** to save the HTML component.


