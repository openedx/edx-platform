.. _Create Exercises:

############################
Creating Exercises and Tools
############################

************************************
Introduction to  Exercises and Tools
************************************

Studio allows you to create a wide variety of exercises and tools for your course. Many of these exercises and tools have templates in Studio so that you can create them easily. In addition, individual course teams frequently create exercises that don't have templates in Studio. We're striving to make these tools available to all our course teams as well, and we have instructions for creating some of them in this section. 

Depending on the exercise or tool, you'll use an HTML, Problem, or Advanced component. The page for each individual exercise or tool contains an example of each exercise or tool, together with all the files, code, and step-by-step instructions that you need to create the exercise or tool. 

.. note:: Problems must include labels for accessibility. The label generally includes the text of the main question in your problem. Instructions for adding labels appear in the page for each individual problem.

****************************
General Exercises and Tools
****************************

.. list-table::
   :widths: 25 25 50

   * - .. image:: /Images/AnnotationExample.png
          :width: 100
          :alt: Example annotation problem
     - :ref:`Annotation`
     - Annotation problems ask students to respond to questions about a specific block of text. The question appears above the text when the student hovers the mouse over the highlighted text so that students can think about the question as they read.
   * - .. image:: /Images/PollExample.png
          :width: 100
          :alt: Example poll
     - :ref:`Conditional Module`
     -  You can create a conditional module to control versions of content that groups of students see. For example, students who answer "Yes" to a poll question then see a different block of text from the students who answer "No" to that question.
   * - .. image:: /Images/JavaScriptInputExample.png
          :width: 100
          :alt: Example JavaScript problem
     - :ref:`Custom JavaScript`
     - Custom JavaScript display and grading problems (also called *custom JavaScript problems* or *JS Input problems*) allow you to create a custom problem or tool that uses JavaScript and then add the problem or tool directly into Studio.
   * - .. image:: /Images/external-grader-correct.png
          :width: 100
          :alt: Example external grader
     - :ref:`External Grader`
     - An external grader is a service that receives student responses to a problem, processes those responses, and returns feedback and a problem grade to the edX platform. You build and deploy an external grader separately from the edX platform. An external grader is particularly useful for software programming courses where students are asked to submit complex code.
   * - .. image:: /Images/GoogleHangout_WithPeople.png   
          :width: 100
          :alt: Google Hangout
     - :ref:`Google Instant Hangout`
     - You can add the ability for students to participate in instant hangouts directly from your course. With instant hangouts, students can interact through live video and voice, share screens and watch videos together, and collaborate on documents. 
   * - .. image:: /Images/IFrame_1.png
          :width: 100
          :alt: Example IFrame tool
     - :ref:`IFrame`
     - IFrames allow you to integrate ungraded exercises and tools from any Internet site into an HTML component in your course.
   * - .. image:: /Images/LTIExample.png
          :width: 100
          :alt: Example LTI component
     - :ref:`LTI Component`
     - LTI components allow you to add an external learning application or non-PDF textbook to Studio.
   * - .. image:: /Images/CITL_AssmtTypes.png
          :width: 100
          :alt: Example open response assessment
     - :ref:`Open Response Assessment`
     - In open response assessments, students receive feedback on written responses of varying lengths as well as files, such as computer code or images, that the students upload. Open response assessments include self assessment and peer assessment.
   * - .. image:: /Images/PollExample.png
          :width: 100
          :alt: Example poll
     - :ref:`Poll`
     - You can run polls in your course so that your students can share opinions on different questions.
   * - .. image:: /Images/ProblemWithAdaptiveHintExample.png
          :width: 100
          :alt: Example problem with adaptive hint
     - :ref:`Problem with Adaptive Hint`
     - A problem with an adaptive hint evaluates a student's response, then gives the student feedback or a hint based on that response so that the student is more likely to answer correctly on the next attempt. These problems can be text input, multiple choice, numerical input, or math expression input problems.
   * - .. image:: /Images/ProblemWrittenInLaTeX.png
          :width: 100
          :alt: Example problem written in LaTeX
     - :ref:`Problem Written in LaTeX`
     - If you have an problem that is already written in LaTeX, you can use this problem type to easily convert your code into XML.
   * - .. image:: /Images/TextInputExample.png
          :width: 100
          :alt: Example text input problem
     - :ref:`Text Input`
     - In text input problems, students enter text into a response field. The response can include numbers, letters, and special characters such as punctuation marks.
   * - .. image:: /Images/WordCloudExample.png
          :width: 100
          :alt: Example word cloud
     - :ref:`Word Cloud`
     - Word clouds arrange text that students enter - for example, in response to a question - into a colorful graphic that students can see.
   * - .. image:: /Images/CustomPythonExample.png  
          :width: 100
          :alt: Example write-your-own-grader problem
     - :ref:`Write Your Own Grader`
     - In custom Python-evaluated input (also called "write-your-own-grader") problems, the grader uses a Python script that you create and embed in the problem to evaluates a student's response or provide hints. These problems can be any type.
   * - .. image:: /Images/VitalSource.png
          :width: 100
          :alt: VitalSource e-book with highlighted note
     - :ref:`VitalSource`
     - The VitalSource Online Bookshelf e-reader allows students to read, browse, and search content (including figures and notes), as well as work with multiple highlighters and copy notes into external documents.

********************************
Image-Based Exercises and Tools
********************************

.. list-table::
   :widths: 30 25 80

   * - .. image:: /Images/DragAndDropProblem.png
          :width: 100
          :alt: Example drag and drop problem
     - :ref:`Drag and Drop`
     - In drag and drop problems, students respond to a question by dragging text or objects to a specific location on an image.
   * - .. image:: /Images/image-modal.png
          :width: 100
          :alt: Example full screen image tool
     - :ref:`Full Screen Image`
     - The Full Screen Image tool allows a student to enlarge an image in the whole browser window. This is useful when the image contains a large amount of detail and text that is easier to view in context when enlarged.
   * - .. image:: /Images/ImageMappedInputExample.png
          :width: 100
          :alt: Example image mapped input problem
     - :ref:`Image Mapped Input`
     - In an image mapped input problem, students click inside a defined area in an image. You define this area by including coordinates in the body of the problem.
   * - .. image:: /Images/Zooming_Image.png
          :width: 100
          :alt: Example zooming image tool
     - :ref:`Zooming Image`
     - Zooming images allow you to enlarge sections of an image so that students can see the section in detail.

************************************
Multiple Choice Exercises and Tools
************************************

.. list-table::
   :widths: 30 25 80

   * - .. image:: /Images/CheckboxExample.png
          :width: 100
          :alt: Example checkbox problem
     - :ref:`Checkbox`
     - In checkbox problems, the student selects one or more options from a list of possible answers. The student must select all the options that apply to answer the problem correctly.
   * - .. image:: /Images/DropdownExample.png
          :width: 100
          :alt: Example dropdown problem
     - :ref:`Dropdown`
     - Dropdown problems allow the student to choose from a collection of answer options, presented as a dropdown list. Unlike multiple choice problems, whose answers are always visible directly below the question, dropdown problems don't show answer choices until the student clicks the dropdown arrow.
   * - .. image:: /Images/MultipleChoiceExample.png
          :width: 100
          :alt: Example multiple choice problem
     - :ref:`Multiple Choice`
     - In multiple choice problems, students select one option from a list of answer options. Unlike with dropdown problems, whose answer choices don't appear until the student clicks the drop-down arrow, answer choices for multiple choice problems are always visible directly below the question.
   * - .. image:: /Images/MultipleChoice_NumericalInput.png
          :width: 100
          :alt: Example multiple choice and numerical input problem
     - :ref:`Multiple Choice and Numerical Input`
     - You can create a problem that combines a multiple choice and numerical input problems. Students not only select a response from options that you provide, but also provide more specific information, if necessary.

********************************
STEM Exercises and Tools
********************************

.. list-table::
   :widths: 30 25 80

   * - .. image:: /Images/ChemicalEquationExample.png
          :width: 100
          :alt: Example chemical equation problem
     - :ref:`Chemical Equation`
     - Chemical equation problems allow the student to enter text that represents a chemical equation into a text box. The grader evaluates the student's response by using a Python script that you create and embed in the problem.
   * - .. image:: /Images/CircuitSchematicExample_short.png
          :width: 100
          :alt: Example circuit schematic builder problem
     - :ref:`Circuit Schematic Builder`
     - In circuit schematic builder problems, students can arrange circuit elements such as voltage sources, capacitors, resistors, and MOSFETs on an interactive grid. They then submit a DC, AC, or transient analysis of their circuit to the system for grading.
   * - .. image:: /Images/GeneExplorer.png
          :width: 100
          :alt: Example gene explorer problem
     - :ref:`Gene Explorer`
     - The Gene Explorer (GeneX) simulates the transcription, splicing, processing, and translation of a small hypothetical eukaryotic gene. GeneX allows students to make specific mutations in a gene sequence, and it then calculates and displays the effects of the mutations on the mRNA and protein.
   * - .. image:: /Images/MathExpressionInputExample.png
          :width: 100
          :alt: Example math expression input problem
     - :ref:`Math Expression Input`
     - The more complex of Studio's two types of math problems. In math expression input problems, students enter mathematical expressions to answer a question. These problems can include unknown variables and more complex symbolic expressions. You can specify a correct answer either explicitly or by using a Python script. 
   * - .. image:: /Images/Molecule_Editor.png
          :width: 100
          :alt: Example molecule editor problem
     - :ref:`Molecule Editor`
     - The molecule editor allows students to draw molecules that follow the rules for covalent bond formation and formal charge, even if the molecules are chemically impossible, are unstable, or do not exist in living systems.
   * - .. image:: /Images/image292.png
          :width: 100
          :alt: Example numerical input problem
     - :ref:`Numerical Input`
     - The simpler of Studio's two types of math problems. In numerical input problems, students enter numbers or specific and relatively simple mathematical expressions to answer a question. You can specify a margin of error, and you can specify a correct answer either explicitly or by using a Python script.
   * - .. image:: /Images/Periodic_Table.png
          :width: 100
          :alt: Example periodic table problem
     - :ref:`Periodic Table`
     - An interactive periodic table of the elements shows detailed information about each element as the student moves the mouse over the element.
   * - .. image:: /Images/ProteinBuilder.png
          :width: 100
          :alt: Example protein builder problem
     - :ref:`Protein Builder`
     - The Protex protein builder asks students to create specified protein shapes by stringing together amino acids. 