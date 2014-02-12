.. _Specialized Problems:

Specialized Problems
====================

Specialized problems are advanced problems such as annotations. These problems are available through the Advanced component in Studio. To add the Advanced component to your course, you'll modify your course's advanced settings. The Advanced component then appears under **Add New Component** in each unit.

-  :ref:`Annotation` Annotation problems ask students to respond to
   questions about a specific block of text. The question appears above
   the text when the student hovers the mouse over the highlighted text
   so that students can think about the question as they read.
- :ref:`Word Cloud` Word clouds arrange text that students enter - for example, in response to a question - into a colorful graphic that students can see. 

.. _ Add Advanced Component:

**Add the Advanced Component to Your Course**

By default, when you create a new component in Studio, you see the
following options.

.. image:: Images/AddNewComponent.gif
  :alt: Image of the Add a New Component panel

To create a specialized problem, you must first add the Advanced
component to your course. To do this, follow these steps.

#. On the **Settings** menu, click **Advanced Settings**.

#. On the **Advanced Settings** page, locate the **Manual Policy
   Definition** section, and then locate the **advanced_modules**
   policy key (this key is at the top of the list).

   .. image:: Images/AdvancedModulesEmpty.gif
     :alt: Image of the Manual Policy Definition section of the Advanced Settings page

#. Under **Policy Value**, place your cursor between the brackets, and
   then enter the value for the type of problem that you want to create.
   Make sure to include the quotation marks, but not the period.

   -  For annotations, enter **"annotatable"**.

   -  For word clouds, enter **"word_cloud"**.

   You can enter more than one problem type at a time. When you do,
   make sure to surround each problem type with quotation marks and
   separate each problem type with a comma, but do not include any
   spaces.
   
   For example, if you wanted to add annotations and word cloud problems in your course, you would enter
   the following between the brackets.

   ::

       "annotatable","word_cloud"

   .. image:: Images/AdvSettings_Before.png
     :alt: Image of the Manual Policy Definition section of the Advanced Settings page, with specialized problems added

#. At the bottom of the page, click **Save Changes**.

   The page refreshes automatically. At the top of the page, you see a
   notification that your changes have been saved.

   The text in the **Policy Value** field now appears as follows.

   .. image:: Images/AdvSettings_After.png
     :alt: Image of the Manual Policy Definition section of the Advanced Settings page, with specialized problems added after saving

#. Return to the unit where you want to add the specialized problem. The
   list of possible components now contains an Advanced component.

   .. image:: Images/AdvancedComponent.gif
     :alt: Image of the Add a New Component panel with the Advanced component option

When you click the Advanced component, you see the following list.

.. image:: Images/SpecProbs_List.gif
  :alt: Image of the Advanced component list

You can now create annotations, open response assessments, and word
clouds in your course. More information about how to create each problem
is provided in the page for that problem type.

.. _Annotation:

Annotation
----------


In an annotation problem, the instructor highlights specific text
inside a larger text block and then asks questions about that text. The
questions appear when students hover the mouse over the highlighted
text. The questions also appear in a section below the text block, along
with space for students' responses.

.. image:: Images/AnnotationExample.gif
  :alt: Image of an annotation problem

Create an Annotation Problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


To create an annotation problem:

Add the Annotation advanced component. To do this, add the "annotatable"
key value to the **Advanced Settings** page. (For more information, see
the instructions in :ref:`Specialized Problems`.)

Add the **Instructions** and **Guided Discussion** segments of the
problem.


#. In the unit where you want to create the problem, click **Advanced**
   under **Add New Component**.
#. In the list of problem types, click **Annotation**.
#. In the component that appears, click **Edit**.
#. In the component editor, replace the example code with your own code.
#. Click **Save**.


Add the **Annotation problem** segment of the problem.


#. Under the Annotation component, create a new blank Advanced Problem
   component.
#. Paste the following code in the Advanced Problem component, replacing
   placeholders with your own information.


       ::

           <problem>
            <annotationresponse>
            <annotationinput>
            <text>PLACEHOLDER: Text of annotation</text>
            <comment>PLACEHOLDER: Text of question</comment>
            <comment_prompt>PLACEHOLDER: Type your response below:</comment_prompt>
            <tag_prompt>PLACEHOLDER: In your response to this question, which tag below 
            do you choose?</tag_prompt>
            <options>
            <option choice="incorrect">PLACEHOLDER: Incorrect answer (to make this 
            option a correct or partially correct answer, change choice="incorrect" 
            to choice="correct" or choice="partially-correct")</option>
            <option choice="correct">PLACEHOLDER: Correct answer (to make this option 
            an incorrect or partially correct answer, change choice="correct" to 
            choice="incorrect" or choice="partially-correct")</option>
            <option choice="partially-correct">PLACEHOLDER: Partially correct answer 
            (to make this option a correct or partially correct answer, 
            change choice="partially-correct" to choice="correct" or choice="incorrect")
            </option>
            </options>
            </annotationinput>
            </annotationresponse>
            <solution>
            <p>PLACEHOLDER: Detailed explanation of solution</p>
            </solution>
           </problem>

#. Click **Save**.


