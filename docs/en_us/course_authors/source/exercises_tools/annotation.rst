.. _Annotation:

###################
Annotation Problem
###################

In an annotation problem, the instructor highlights specific text inside a larger text block and then asks questions about that text. The questions appear when students hover the mouse over the highlighted text. The questions also appear in a section below the text block, along with space for students' responses.

Annotation problems ask students to respond to questions about a specific block of text. The question appears above the text when the student hovers the mouse over the highlighted text so that students can think about the question as they read.

.. image:: /Images/AnnotationExample.png
  :alt: Annotation problem

****************************
Create an Annotation Problem
****************************

To create an annotation problem, you'll add the Annotation advanced component to your course, add the **Instructions** and **Guided Discussion** segments of the problem, and then the **Annotation problem** segment of the problem.

#. Add the Annotation advanced component. 

    #. From the **Settings** menu select **Advanced Settings**.

    #. In the field for the **Advanced Module List** policy key, place your
       cursor between the brackets.

    #. Enter the following value. Make sure to include the quotation marks.

       ``"annotatable"``

    4. At the bottom of the page, click **Save Changes**.

       The page refreshes automatically. At the top of the page, you see a
       notification that your changes have been saved.

    5. Return to the unit where you want to add the specialized problem. The
       list of possible components now contains an Advanced component.

       .. image:: /Images/AdvancedComponent.png
          :alt: Image of the Add a New Component panel with the Advanced component option

2. Add the **Instructions** and **Guided Discussion** segments of the
problem.

    #. In the unit where you want to create the problem, under **Add New
       Component** click **Advanced**.
    #. In the list of problem types, click **Annotation**.
    #. In the component that appears, click **Edit**.
    #. In the component editor, replace the example code with your own code.
    #. Click **Save**.

3. Add the **Annotation problem** segment of the problem.

    #. Under the Annotation component, create a new blank Advanced Problem
       component.
       
    #. Paste the following code in the Advanced Problem component, replacing
       placeholders with your own information.

        .. code-block:: xml

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


