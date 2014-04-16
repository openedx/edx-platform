.. _Peer Assessments:

########################
Peer Assessments
########################

********************************
Introduction to Peer Assessments
********************************

.. note:: **The peer assessment feature is in limited release.** If you're at an edX consortium university and you plan to include peer assessments in a MOOC, you'll work with your edX project manager (PM) to enable the peer assessment feature and create peer assessment assignments.

Peer assessments allow instructors to assign questions that may not have definite answers. Students submit a response to a question, and then compare their peers' responses to a rubric that you create. Peer assessment problems also include self assessments, in which students compare their own responses to the rubric.

For more information, see the following sections:

* :ref:`PA Elements`
* :ref:`PA Scoring`
* :ref:`PA Create a PA Problem`
* :ref:`PA Access Status`

.. _PA Elements:

********************************
Elements of a Peer Assessment
********************************

When you create a peer assessment problem, you'll specify several elements:

* The number of responses and assessments.
* The assessment type or types.
* The due dates for each step (optional).
* The question.
* The rubric.

For step-by-step instructions, see :ref:`PA Create a PA Problem`.


Number of Responses and Assessments
***********************************

In the problem code, you'll indicate the **number of responses** each student has to assess and the **number of peer assessments** each response has to receive.

.. note:: Because some students may submit a response but not complete peer assessments, some responses may not receive the required number of assessments. To increase the chance that all responses will receive enough assessments, you must set the number of responses that students have to assess to be higher than the number of assessments that each response must undergo. For example, if you require each response to receive three assessments, you could require each student to assess five responses.

If all responses have received assessments, but some students haven't completed the required number of peer assessments, those students can assess responses that other students have already assessed. The student who submitted the response sees the additional peer assessments when he sees his score. However, the additional peer assessments do not count toward the score that the response receives.

For more information, see :ref:`PA Specify Name and Assessment Types`.

Assessment Type
********************

In your problem, you'll also specify the **assessment type or types**. You can see the type and order of the assessments when you look at the problem. In the following example, after students submit a response, they complete peer assessments on other students' responses ("Assess Peers") and then complete self assessments ("Assess Yourself").

.. image:: /Images/PA_Steps_LMS.png
  :alt: Image of peer assessment with assessment types circled

.. note:: In this initial release, the type and order of assessments cannot be changed. Students must complete peer assessments followed by a self assessment.

For more information, see :ref:`PA Specify Name and Assessment Types`.

Start and Due Dates (optional)
******************************

You can specify **start dates** and **due dates** for students to submit responses, perform peer assessments, and perform self assessments.

You can set different dates for each step, and these dates can overlap. For example, you can allow students to submit responses and complete peer and self assessments starting on March 1. You can require all responses to be submitted by March 7, but allow students to continue peer and self assessments until March 14, a week after all responses are due.

If you don't specify dates, the deadline for all elements--responses, peer assessments, and self assessments--is the due date that you set for the subsection that contains the peer assessment. If you do specify dates, those dates take precedence over the subsection due date.

.. note:: We don't recommend that you use the same due date and time for response submissions and assessments. If a student submits a response immediately before the due date, other students will have very little time to assess the response before peer assessment closes. In this case, a student's response may not receive a score.

For more information, see :ref:`PA Add Due Dates`.

Question
************

You'll also specify the **question** that you want your students to answer. This appears near the top of the component, followed by a field where the student enters a response.

When you write your question, you can include helpful information for your students, such as what students can expect after they submit responses and the approximate number of words or sentences that a student's response should have. (A response cannot have more than 10,000 words.) 

For more information, see :ref:`PA Add Question`.

.. _PA Rubric:

Rubric
*********

Your problem must include a **rubric** that you design. The same rubric is used for peer and self assessments, and the rubric appears when students begin grading. Students compare their peers' responses to the rubric.

Rubrics are made of *criteria* and *options*.

* Each criterion has a *name*, a *prompt*, and two or more *options*. 

   * The name is a very short summary of the criterion, such as Ideas or Content. Criterion names generally have just one word. **The name for each criterion must be unique.** The system uses the criterion name for identification. Criterion names do not appear in the rubric that students see when they are completing peer assessments, but they do appear on the page that shows the student's final grade.

     .. image :: /Images/PA_CriterionName.png
        :alt: Image of a final score page with call-outs for the criterion names

   * The prompt is a description of the criterion. 

* Each option has a *name*, an *explanation*, and a *point value*.

  .. image:: /Images/PA_Rubric_LMS.png
     :alt: Image of a rubric in the LMS with call-outs for the criterion prompt and option names, explanations, and points

When you create your rubric, decide how many points each option will receive, and make sure that the explanation for each option is as specific as possible. For example, one criterion and set of options may resemble the following.

**Criterion**

Name: Origins

Prompt: Does this response explain the origins of the Hundred Years' War? (5 points possible)

**Options**

.. list-table::
   :widths: 8 20 50
   :stub-columns: 1
   :header-rows: 1

   * - Points
     - Name
     - Explanation
   * - 0
     - Not at all
     - This response does not address the origins of the Hundred Years' War.
   * - 1
     - Dynastic disagreement
     - This response alludes to a dynastic disagreement between England and France, but doesn't reference Edward III of England and Philip VI of France.
   * - 3
     - Edward and Philip
     - This response mentions the dynastic disagreement between Edward III and Philip VI, but doesn't address the role of Salic law.
   * - 5
     - Salic law
     - This response explains the way that Salic law contributed to the dynastic disagreement between Edward III and Philip VI, leading to the Hundred Years' War.

For more information about writing effective rubrics, see Heidi Goodrich Andrade's `Understanding Rubrics <http://learnweb.harvard.edu/alps/thinking/docs/rubricar.htm>`_.

Note that different criteria in the same assignment can have different numbers of options. For example, in the image above, the first criterion has three options and the second criterion has four options.

For more information, see :ref:`PA Add Rubric`.

.. _PA Scoring:

***********************
Peer Assessment Scoring
***********************

Peer assessments are scored by criteria. An individual criterion's score is the median of the scores that each peer assessor gave that criterion. For example, if the Ideas criterion in a peer assessment receives a 10 from one student, a 7 from a second student, and an 8 from a third student, the Ideas criterion's score is 8.

A student's final score for a peer assessment is the sum of the median scores for each individual criterion. 

For example, a response may receive the following scores from peer assessors:

.. list-table::
   :widths: 25 10 10 10 10
   :stub-columns: 1
   :header-rows: 1

   * - Criterion Name
     - Peer 1
     - Peer 2
     - Peer 3
     - Median
   * - Ideas (out of 10)
     - 10
     - 7
     - 8
     - **8**
   * - Content (out of 10)
     - 7
     - 9
     - 8
     - **8**
   * - Grammar (out of 5)
     - 4
     - 4
     - 5
     - **4**

To calculate the final score, add the median scores for each criterion:

  **Ideas median (8/10) + Content median (8/10) + Grammar median (4/5) = final score (20/25)**

Note, again, that final scores are calculated by criteria, not by individual assessor. Thus the response's score is not the median of the scores that each individual peer assessor gave the response.

.. _PA Create a PA Problem:

********************************
Create a Peer Assessment Problem
********************************

.. warning:: Peer assessments are in limited release and are only available in a few courses. To enable the peer assessment feature in your course, contact your edX program manager. After the feature has been enabled, you can create peer assessments by following the steps below.

To create a peer assessment problem, you'll edit the XML code in a Problem component, similar to creating other problems. The following image shows what a peer assessment component looks like when you edit it in Studio, as well as the way that students see that peer assessment in the LMS.

.. image:: /Images/PA_All_XML-LMS_small.png
   :alt: Image of a peer assessment in Studio and LMS views

Creating a peer assessment is a multi-step process:

* :ref:`PA Create Component`
* :ref:`PA Specify Name and Assessment Types`
* :ref:`PA Add Due Dates`
* :ref:`PA Add Question`
* :ref:`PA Add Rubric`
* :ref:`PA Test Problem`

Each of these steps is covered in detail below.

.. _PA Create Component:

Step 1. Create the Component
****************************

#. In Studio, open the unit where you want to create the assessment.
#. Under **Add New Component**, click **Advanced**, and then click **Peer Assessment**.
#. In the Problem component that appears, click **Edit**.

   The component editor opens, and you can see sample code that includes the assignment's title, the assessment type or types, the number of assessments that students must complete, a sample question ("prompt"), and a rubric. You'll replace this sample content with the content for your problem in the next steps.

   Note that you won't use the **Settings** tab in the component editor when you create peer assessments.

.. _PA Specify Name and Assessment Types:

Step 2. Specify the Problem Name and Assessment Types
*****************************************************

To specify problem data such as the name and assessment types, you'll work with the XML at the top of the problem.

Locate the following XML near the top of the component editor:

.. code-block:: xml

  <openassessment>
  <title></title>
  <assessments>
    <assessment name="peer-assessment" must_grade="5" must_be_graded_by="3"/>
    <assessment name="self-assessment"/>
  </assessments>

This code specifies four elements:

* **The title of the assignment**. In this example, because there is no text between the ``<title>`` tags, the assignment does not have a specified title.
* **The type and order of the assessments**. This information is in the **name** attribute in the two ``<assessment>`` tags. The peer assessment runs, and then the student performs a self assessment. (Note that in this initial release, students must complete a peer assessment followed by a self assessment. The assessment types and order cannot be changed.) 
* **The number of responses that each student must assess** (for peer assessments). This information is in the **must_grade** attribute in the ``<assessment>`` tag for the peer assessment. In this example, each student must grade five peer responses before he receives the scores that his peers have given him. 
* **The number of peer assessments each response must receive** (for peer assessments). This information is in the **must_be_graded_by** attribute in the ``<assessment>`` tag for the peer assessment. In this example, each response must receive assessments from three students before it can return to the student who submitted it. 

To specify your problem data, follow these steps.

#. Between the ``<title>`` tags, add a name for the problem.

#. In the ``<assessment>`` tag that contains "**peer-assessment**", replace the values for **must_grade** and **must_be_graded_by** with the numbers that you want.

.. note:: The value for **must_grade** must be greater than or equal to the value for **must_be_graded_by**.

.. _PA Add Due Dates:

Step 3. Add Start and Due Dates (optional)
******************************************

.. note:: Setting start and due dates is optional. If you don't specify dates, the deadline for all student responses and assessments is the due date that you set for the subsection that contains the peer assessment. If you do specify dates, those dates take precedence over the subsection due date.

To specify due dates and times, you'll add code that includes the date and time inside the XML tags for the problem and for each specific assessment. The date and time must be formatted as ``YYYY-MM-DDTHH:MM:SS``.

.. note:: You must include the "T" between the date and the time, with no spaces. All times are in universal coordinated time (UTC).

* To specify a due date for response submissions, add the ``submission_due`` attribute with the date and time to the ``<openassessment>`` tag (this is the first tag in your problem).

  ``<openassessment submission_due="YYYY-MM-DDTHH:MM:SS">``

* To specify start and end times for an assessment, add ``start`` and ``due`` attributes with the date and time to the ``<assessment>`` tags for the assessment.

  ``<assessment name="peer-assessment" must_grade="5" must_be_graded_by="3" start="YYYY-MM-DDTHH:MM:SS" due="YYYY-MM-DDTHH:MM:SS"/>``

  ``<assessment name="self-assessment" start="YYYY-MM-DDTHH:MM:SS" due="YYYY-MM-DDTHH:MM:SS"/>``

For example, the code for your problem may resemble the following.

.. code-block:: xml

  <openassessment submission_due="2014-03-01T00:00:00">
  <assessments>
    <assessment name="peer-assessment" must_grade="5" must_be_graded_by="3" start="2014-02-24T00:00:00" due="2014-03-08T00:00:00"/>
    <assessment name="self-assessment" start="2014-02-24T00:00:00" due="2014-03-08T00:00:00"/>
  </assessments>

In this example, the problem is set at the subsection level to open on February 24, 2014 at midnight UTC. (This information does not appear in the code.) Additionally, the code specifies the following:

* Students must can begin submitting responses on February 24, 2014 at midnight UTC, and must submit all responses before March 1, 2014 at midnight UTC:

  ``<openassessment submission_due="2014-03-01T00:00:00">``

* Students can begin peer assessments on February 24, 2014 at midnight UTC, and all peer assessments must be complete by March 8, 2014 at midnight UTC:

  ``<assessment name="peer-assessment" must_grade="5" must_be_graded_by="3" start="2014-02-24T00:00:00" due="2014-03-08T00:00:00"/>``

* Students can begin self assessments on February 24, 2014 at midnight UTC, and all self assessments must be complete by March 8, 2014 at midnight UTC:

  ``<assessment name="self-assessment" start="2014-02-24T00:00:00" due="2014-03-08T00:00:00"/>``


.. note:: We don't recommend that you use the same due date and time for response submissions and peer assessments. If a student submits a response immediately before the due date, other students will have very little time to assess the response before peer assessment closes. In this case, a student's response may not receive a score.

.. _PA Add Question:

Step 4. Add the Question
********************************

The following image shows a question in the component editor, followed by the way the question appears to students.

.. image:: /Images/PA_Question_XML-LMS.png
      :alt: Image of question in XML and the LMS

To add the question:

#. In the component editor, locate the ``<prompt>`` tags.

#. Replace the sample text between the ``<prompt>`` tags with the text of your question. Note that the component editor respects paragraph breaks inside the ``<prompt>`` tags. You don't have to add ``<p>`` tags to create individual paragraphs.

In this initial release, you cannot add text formatting or images in the Peer Assessment component. If you want to include text formatting or images in the text of your prompt, you can add an HTML component above the Peer Assessment component. The following image shows an HTML component that contains an image and the quote by Katherine Paterson, followed by a Peer Assessment component that contains the introductory text ("This problem requires...") and the text that appears between the ``<prompt>`` tags in the Peer Assessment component ("Write a persuasive essay...").

.. image:: /Images/PA_HTML-PA_LMS.png
      :alt: Image of a peer assessment that has an image in an HTML component

.. _PA Add Rubric:

Step 5. Add the Rubric
********************************

To add the rubric, you'll create your criteria and options in XML. The following image shows a highlighted criterion and its options in the component editor, followed by the way the criterion and options appear to students.

.. image:: /Images/PA_RubricSample_XML-LMS.png
      :alt: Image of rubric in XML and the LMS, with call-outs for criteria and options

For more information about criteria and options, see :ref:`PA Elements`.

To add the rubric:

#. In the component editor, locate the following XML. This XML contains a single criterion and its options. You'll replace the placeholder text with your own content.  

	.. code-block:: xml

	      <criterion>
	      <name>Ideas</name>
	      <prompt>Determine if there is a unifying theme or main idea.</prompt>
	      <option points="0">
	        <name>Poor</name>
	        <explanation>Difficult for the reader to discern the main idea.
	                Too brief or too repetitive to establish or maintain a focus.</explanation>
	      </option>
	      <option points="3">
	        <name>Fair</name>
	        <explanation>Presents a unifying theme or main idea, but may
	                include minor tangents.  Stays somewhat focused on topic and
	                task.</explanation>
	      </option>
	      <option points="5">
	        <name>Good</name>
	        <explanation>Presents a unifying theme or main idea without going
	                off on tangents.  Stays completely focused on topic and task.</explanation>
	      </option>
	    </criterion>

   .. note:: The placeholder text contains indentations and line breaks. You don't have to preserve these indentations and line breaks when you replace the placeholder text. 

#. Under the opening ``<criterion>`` tag, replace the text between the ``<name>`` tags with the name of your criterion. Then, replace the text between the ``<prompt>`` tags with the description of that criterion.

   Note that **every criterion must have a unique name.** The system uses the criterion name for identification. For more information about criteria, see :ref:`PA Rubric`.

#. Inside the first ``<option>`` tag, replace the value for ``points`` with the number of points that you want this option to receive.

#. Under the ``<option>`` tag, replace the text between the ``<name>`` tags with the name of the first option. Then, replace the text between the ``<explanation>`` tags with the description of that option.

#. Use this format to add as many options as you want.

You can use the following code as a template:

.. code-block:: xml

	 <criterion>
	   <name>NAME</name>
	   <prompt>PROMPT TEXT</prompt>
	   <option points="NUMBER">
	     <name>NAME</name>
	     <explanation>EXPLANATION</explanation>
	   </option>
	   <option points="NUMBER">
	     <name>NAME</name>
	     <explanation>EXPLANATION</explanation>
	   </option>
	   <option points="NUMBER">
	     <name>NAME</name>
	     <explanation>EXPLANATION</explanation>
	   </option>
	 </criterion>


.. _PA Test Problem:

Step 6. Test the Problem
********************************

To test your assignment, set up the assignment in a test course, and ask a group of beta users to submit responses and grade each other. The beta testers can then let you know if they found the question and the rubric easy to understand or if they found any problems with the assignment.

.. _PA Access Status:

******************************
Access Status of Problem Steps
******************************

After your problem has opened, you can check the current number of students who are in each step--that is, how many students have submitted responses, have completed peer and self assessments, are waiting to assess responses or receive grades, or have finished the problem entirely. 

To find this information, open the problem in the LMS, scroll to the bottom of the problem, and then click the black **Course Staff Information** banner.

.. image:: /Images/PA_CourseStaffInfo_Collapsed.png
   :alt: The Course Staff Information banner at the bottom of the peer assessment

**Course Staff Information** expands, and you can see the number of students who are actively in each step of the problem.

.. image:: /Images/PA_CourseStaffInfo_Expanded.png
   :alt: The Course Staff Information box expanded, showing problem status



