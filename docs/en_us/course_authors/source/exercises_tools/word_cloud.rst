.. _Word Cloud:

##################
Word Cloud Tool
##################


In a word cloud tool, students enter words into a field in response
to a question or prompt. The words all the students have entered then
appear instantly as a colorful graphic, with the most popular responses
appearing largest. The graphic becomes larger as more students answer.
Students can both see the way their peers have answered and contribute
their thoughts to the group.


For example, the following word cloud was created from students'
responses to a question in a HarvardX course.

.. image:: /Images/WordCloudExample.png
  :alt: Image of a word cloud problem

****************************
Create a Word Cloud Tool
****************************

To create a word cloud tool:

#. Add the Word Cloud advanced component. 

    #. On the **Settings** menu, click **Advanced Settings**.

    #. On the **Advanced Settings** page, locate the **Manual Policy Definition** section, and then locate the **advanced_modules** policy key (this key is at the top of the list).

    #. Under **Policy Value**, place your cursor between the brackets, and
       then enter the following. Make sure to include the quotation marks.

       ``"word_cloud"``

    #. At the bottom of the page, click **Save Changes**.

       The page refreshes automatically. At the top of the page, you see a
       notification that your changes have been saved.

    #. Return to the unit where you want to add the specialized problem. The
       list of possible components now contains an Advanced component.

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
