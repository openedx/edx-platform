.. _Drag and Drop:

##########################
Drag and Drop Problem
##########################

In drag and drop problems, students respond to a question by dragging text or objects to a specific location on an image.

.. image:: /Images/DragAndDropProblem.png
 :alt: Image of a drag and drop problem

*********************************
Create a Drag and Drop Problem
*********************************

To create a simple drag and drop problem in which students drag labels onto an image, you'll upload the image that you want students to drag labels onto, and then create a Problem component.

#. On the **Files & Uploads** page, upload your image file. For more information about uploading files, see :ref:`Add Files to a Course`.
#. In the unit where you want to create the problem, click **Problem** under **Add New Component**, and then click the **Advanced** tab.
#. Click **Drag and Drop**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example text with the text of your problem.
#. In the ``<drag_and_drop_input>`` tag, replace **https://studio.edx.org/c4x/edX/DemoX/asset/L9_buckets.png** with the URL of your image file on the **Files & Uploads** page (for example, **/static/Image.png**). 
#. For at least one ``<draggable>`` tag, replace the text of the **label** attribute with the text of the label you want students to drag. For example, if you want students to drag the word "Iceland" onto your image, the new tag would resemble the following:
   
   ``<draggable id="1" label="Iceland"/>``

8. Repeat the previous step for all the labels that you want to use. Make sure that the **id** attribute is different for each ``<draggable>`` tag.
#. Determine the coordinates and radius of the correct area on the image.  
#. Under ``correct_answer = {``, add an entry for each label, using the following format. These values are in pixels:

    ``'id':    [[x coordinate, y coordinate], radius]``

    For example, if your image is 600 pixels wide and 400 pixels high, and you want your students to drag the Iceland label to an area in the upper-left part of the image and drag a Sweden label near the lower-right part of your image, the code would resemble the following (where 2 is the ID for the Sweden label):

    .. code-block:: xml

        correct-answer = {
                '1':    [[50, 50], 75]
                '2':    [[550, 350], 75]}

    .. note:: Make sure the code contains the closing curly brace (**}**). 
#. Click **Save**.

==========================================
Sample Drag and Drop Problem Code
==========================================

To create the drag and drop problem that appears in the image above, you'll download two files from edX, upload these files to to the **Files & Uploads** page, and then add the code for the problem to a Problem component.

#. Download the following files from edX:

  * Allopurinol.gif
  * AllopurinolAnswer.gif

  To download both these files in a .zip archive, click http://files.edx.org/DragAndDropProblemFiles.zip.

2. Upload the Allopurinol.gif and AllopurinolAnswer.gif files to the **Files & Uploads** page.
#. In the unit where you want to create the problem, click **Problem** under **Add New Component**, and then click the **Advanced** tab.
#. Click **Drag and Drop**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with the following code.
#. Click **Save**.

**Problem Code**:

.. code-block:: xml

  <problem>
    <p> Allopurinol is a drug used to treat and prevent gout, a very painful form of arthritis. Once only a “rich man’s disease”, gout has become more and more common in recent decades – affecting about 3 million people in the United States alone. Deposits of needle-like crystals of uric acid in connective tissue or joint spaces cause the symptoms of swelling, stiffness and intense pain. Individuals with gout overproduce uric acid because they cannot eliminate it efficiently. Allopurinol treats and prevents gout by stopping the overproduction of uric acid through inhibition of an enzyme required for the synthesis of uric acid. </p>
    <p> You are shown one of many possible molecules. On the structure of allopurinol below, identify the functional groups that are present by dragging the functional group name listed onto the appropriate target boxes on the structure. If you want to change an answer, you have to drag off the name as well. You may need to scroll through the names of functional groups to see all options. </p>
    <customresponse>
      <drag_and_drop_input no_labels="true" one_per_target="true" target_outline="true" img="/static/Allopurinol.gif">
        <draggable can_reuse="true" label="methyl" id="1"/>
        <draggable can_reuse="true" label="hydroxyl" id="2"/>
        <draggable can_reuse="true" label="amino" id="3"/>
        <draggable can_reuse="true" label="carboxyl" id="4"/>
        <draggable can_reuse="true" label="aldehyde" id="5"/>
        <draggable can_reuse="true" label="phosphate" id="6"/>
        <draggable can_reuse="true" label="sulfhydryl" id="7"/>
        <draggable can_reuse="true" label="phenyl" id="8"/>
        <draggable can_reuse="true" label="none" id="none"/>
        <target id="0" h="53" w="66" y="55.100006103515625" x="131.5"/>
        <target id="1" h="113" w="55" y="140.10000610351562" x="181.5"/>
      </drag_and_drop_input>
      <answer type="loncapa/python"> 
  correct_answer = [ {'draggables': ['2'], 'targets': ['0' ], 'rule':'unordered_equal' }, 
  {'draggables': ['none'], 'targets': ['1' ], 'rule':'unordered_equal' }] 
  if draganddrop.grade(submission[0], correct_answer): 
      correct = ['correct'] 
  else: 
      correct = ['incorrect'] 
      </answer>
    </customresponse>
    <solution>
      <img src="/static/AllopurinolAnswer.gif"/>
    </solution>
  </problem>


.. _Drag and Drop Problem XML:

*********************************
Drag and Drop Problem XML
*********************************

================================
Template for Simple Problem
================================

.. code-block:: xml

  <problem>
  <p>PROBLEM TEXT</p>
   <customresponse>
        <drag_and_drop_input img="/static/TARGET_IMAGE.png">
            <draggable id="1" label="LABEL 1"/>
            <draggable id="2" label="LABEL 2"/>
        </drag_and_drop_input>
        <answer type="loncapa/python">
  correct_answer = {
          '1':      [[x, y], radius],
          '2':      [[x, y], radius]}
  if draganddrop.grade(submission[0], correct_answer):
      correct = ['correct']
  else:
      correct = ['incorrect']
          </answer>
      </customresponse>


================================
Template for Advanced Problem
================================

.. code-block:: xml

  <problem>
      <customresponse>
          <text>
              <p>PROBLEM TEXT</p>
          </text>
          <drag_and_drop_input img="/static/TARGET_IMAGE.png" target_outline="true" one_per_target="true" no_labels="true" label_bg_color="rgb(222, 139, 238)">
              <draggable id="1" label="LABEL 1" />
              <draggable id="2" label="LABEL 2" />
              <target id="A" x="NUMBER" Y="NUMBER" w="X+WIDTH" h="Y+HEIGHT"/>
              <target id="B" x="NUMBER" Y="NUMBER" w="X+WIDTH" h="Y+HEIGHT"/>
          </drag_and_drop_input>
          <answer type="loncapa/python">
  correct_answer = [{
      'draggables': ['1', '2'],
      'targets': ['A', 'B' ],
      'rule':'anyof'
  }]
  if draganddrop.grade(submission[0], correct_answer):
      correct = ['correct']
  else:
      correct = ['incorrect']
          </answer>
      </customresponse>
  </problem>

========
Tags
========

* ``<customresponse>``: Indicates that the problem is a custom response problem.
* ``<drag_and_drop_input/>``: Indicates the custom response problem is a drag and drop problem.
* ``<draggable/>``: Specifies a single object that a student will drag onto the base image.
* ``<target>``: Specifies the location on the base image where a draggable must be dropped.

**Tag:** ``<drag_and_drop_input/>``

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - img (required)
       - Relative path to an image that will be the base image. All draggables can be dragged onto it.
     * - target_outline 
       - Specifies whether an outline (gray dashed line) should be drawn around targets (if they are specified). It can be either 'true' or 'false'. If not specified, the targets do not have outlines.
     * - one_per_target 
       - Specify whether to allow more than one draggable to be placed onto a single target. It can be either 'true' or 'false'. If not specified, the default value is 'true'.
     * - no_labels (required)
       - default is false, in default behaviour if label is not set, label is obtained from id. If no_labels is true, labels are not automatically populated from id, and one can not set labels and obtain only icons.

  Children

     * ``<draggable>``
     * ``<target>``

**Tag:** ``<draggable/>``

Specifies a single draggable object in a drag and drop problem.

A draggable is what the user must drag out of the slider and drop onto the base image. After a drag operation, if the center of the draggable is located outside the rectangular dimensions of the image, it will be returned to the slider.

For the grader to work, each draggable must have a unique ID.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - id (required)
       - Unique identifier of the draggable object.
     * - label (optional)
       - Text label that the user sees.
     * - icon (optional)
       - For draggables that are images, the relative path to the image file.
     * - can_reuse
       - true or false, default is false. If true, same draggable can be used multiple times.

  Children
  
  (none)

**Tag:** ``<target>``

Specifies the location on the base image where a student must drop a draggable item. By design, if the center of a draggable lies within the target (i.e. in the rectangle defined by [[x, y], [x + w, y + h]],  it is within the target. Otherwise, it is outside.

If you specify at least one target, and a student drops a draggable item on a location that is outside a target, the draggable item returns to the slider.

If you don't specify a target, a student can drop a draggable item anywhere on the base image.

  Attributes

  .. list-table::
     :widths: 20 80

     * - Attribute
       - Description
     * - id (required)
       - Unique identifier of the target object.
     * - x
       - X-coordinate on the base image where the top left corner of the target will be positioned.
     * - y
       - Y-coordinate on the base image where the top left corner of the target will be positioned.
     * - w
       - Width of the target, in pixels.
     * - h
       - Height of the target, in pixels.

  Children

  (none)


For more information about how to create drag and drop problems, see `XML Format of Drag and Drop Input
<https://edx.readthedocs.org/en/latest/course_data_formats/drag_and_drop/drag_and_drop_input.html>`_.

