.. _Image Mapped Input:

###########################
Image Mapped Input Problem
###########################

In an image mapped input problem, students click inside a defined area in an image. You define this area by including coordinates in the body of the problem.

.. image:: /Images/ImageMappedInputExample.png
 :alt: Image of an image mapped input problem

****************************************
Create an Image Mapped Input Problem
****************************************

To create a image mapped input problem:

#. In the unit where you want to create the problem, click **Problem**
   under **Add New Component**, and then click the **Advanced** tab.
#. Click **Image Mapped Input**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.

**Problem Code**:

.. code-block:: xml

  <problem>
    <p><b>Example Problem</b></p>
     <startouttext/>
      <p>In the image below, click the triangle.</p>
      <endouttext/>
      <imageresponse>
      <imageinput src="/static/threeshapes.png" width="220" height="150" rectangle="(80,40)-(130,90)" />
      </imageresponse>
  </problem>


.. _Image Mapped Input Problem XML:

******************************
Image Mapped Input Problem XML 
******************************

==========
Template
==========

.. code-block:: xml

  <problem>
    <startouttext/>
      <p>In the image below, click the triangle.</p>
    <endouttext/>
        <imageresponse>
         <imageinput src="IMAGE FILE PATH" width="NUMBER" height="NUMBER" rectangle="(X-AXIS,Y-AXIS)-(X-AXIS,Y-AXIS)" />
        </imageresponse>
  </problem>

=====
Tags
=====

* ``<imageresponse>``: Indicates that the problem is an image mapped input problem.
* ``<imageinput>``: Specifies the image file and the region in the file that the student must click.

**Tag:** ``<imageresponse>``

Indicates that the problem is an image mapped input problem.

  Attributes

  (none)

  Children

  * ``<imageinput>``

**Tag:** ``<imageinput>``

Specifies the image file and the region in the file that the student must click.

  Attributes

   .. list-table::
      :widths: 20 80

      * - Attribute
        - Description
      * - src (required)
        - The URL of the image
      * - height (required)
        - The height of the image, in pixels
      * - width (required)
        - The width of the image, in pixels
      * - rectangle (required)
        - An attribute with four embedded values in the format (<start_width>,<start_height>)-(<end_width>,<end-height>). All coordinates start with (0,0) in the top left corner and increase in value toward the bottom right corner, very similar to the progression of reading English. The two coordinates defined form the two opposite corners of a box which a student can click inside of.

  Children
  
  (none)

