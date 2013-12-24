.. _Tools:


#############################
Working with Tools
#############################

***************************
Overview of Tools in Studio
***************************

**Intro to Tools text** - you can use various tools in Studio, etc. (Sometimes
called blades, though that's not intuitive for very many people.)

- :ref:`Qualtrics Survey`
- Interactive periodic table (if we document this)
- :ref:`Word Cloud`
- :ref:`Zooming image`


.. _Qualtrics Survey:

****************
Qualtrics Survey
****************

**description of Qualtrics survey and explanation of why course teams would want to
use it**

**image of Qualtrics survey**

Create a Qualtrics Survey
~~~~~~~~~~~~~~~~~~~~~~~~~

To create a Qualtrics survey, you'll use the Anonymous User ID template. This
template contains HTML with instructions.

#. Under **Add New Component**, click **html**, and then click **Anonymous User ID**.

#. In the empty component that appears, click **Edit**.

#. When the component editor opens, replace the example content with your own content.

   - **flesh these instructions out more**

   - To use your survey, you must edit the link in the template to include your university and survey ID.

   - You can also embed the survey in an iframe in the HTML component.

   - For more details, read the instructions in the HTML view of the component.

#. Click **Save** to save the HTML component.


.. _Word Cloud:

**********
Word Cloud
**********


In a word cloud problem, students enter words into a field in response
to a question or prompt. The words all the students have entered then
appear instantly as a colorful graphic, with the most popular responses
appearing largest. The graphic becomes larger as more students answer.
Students can both see the way their peers have answered and contribute
their thoughts to the group.


For example, the following word cloud was created from students'
responses to a question in a HarvardX course.

.. image:: Images/WordCloudExample.gif

Create a Word Cloud Exercise
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a word cloud exercise:


#. Add the Word Cloud advanced component. To do this, add the
   "word_cloud" key value to the **Advanced Settings** page. (For more
   information, see the instructions in :ref:`Specialized Problems`.)
#. In the unit where you want to create the problem, click **Advanced**
   under **Add New Component**.
#. In the list of problem types, click **Word Cloud**.
#. In the component that appears, click **Edit**.
#. In the component editor, specify the settings that you want. You can
   leave the default value for everything except **Display Name**.


   -  **Display Name**: The name that appears in the course ribbon and
      as a heading above the problem.
   -  **Inputs**: The number of text boxes into which students can enter
      words, phrases, or sentences.
   -  **Maximum Words**: The maximum number of words that the word cloud
      displays. If students enter 300 different words but the maximum is
      set to 250, only the 250 most commonly entered words appear in the
      word cloud.
   -  **Show Percents**: The number of times that students have entered
      a given word as a percentage of all words entered appears near
      that word.


#. Click **Save**.


For more information, see `Xml Format of "Word Cloud" Module
<https://edx.readthedocs.org/en/latest/course_data_formats/word_cloud/word_cloud.html#>`_.

.. _Zooming Image:

******************
Zooming Image Tool
******************

To create a new HTML component in an existing unit, ensure the unit is private.
For more information on public and private units, see :ref:`Public and Private Units`.

Some edX classes use extremely large, extremely detailed graphics. To make it
easier to understand we can offer two versions of those graphics, with the zoomed
section showing when you click on the main view.

The example below is from 7.00x: Introduction to Biology and shows a subset of the
biochemical reactions that cells carry out.

.. image:: Images/ZoomingImage.gif

Create a Zooming Image Tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Under **Add New Component**, click **html**, and then click **Zooming Image**.

#. In the empty component that appears, click **Edit**.

#. When the component editor opens, replace the example content with your own content.

#. Click **Save** to save the HTML component.
