.. _Guidelines for Creating Accessible Content

###################################################
Guidelines for Creating Accessible Content
###################################################

 
EdX strives to create an innovative, online-learning platform that promotes accessibility for everyone, including learners with disabilities. 
We intend for these guidelines to help the course teams understand the importance of considering accessibility when designing courses and provide guidance so that they can serve the widest possible audience. 
*Accessibility* in online instruction refers to the degree to which information and activities are available to all students equally, regardless of physical or other disabilities.

Our guidance is based on international standards and principles for web accessibility (W3C WCAG 2.0) and universal design (usable by all, to the greatest extent possible, without the need for adaptation or specialized design). 
Instructors who build courses based on these principles promote the opportunity to create an inclusive experience that considers the diverse set of learning styles and needs of all learners—including learners with disabilities, learners who speak English as a second language, learners with technical issues such as low bandwidth internet or no access to audio, and learners with age-related capability issues. For purposes of these guidelines, we have assumed that end users will be equipped with the appropriate adaptive technology and compatible software.

Occasionally, unanticipated accessibility barriers will arise. 
To supplement the accessibility you can achieve within the edX platform, we recommend that you engage the resources available at your institution to support learners with disabilities. 
Most institutions offer disability support services and information technology resources that provide accessibility advice and support. These professionals are trained in making disability accommodation decisions and can advise you on what accommodations may be appropriate in light of the goals of the course and the inherent instructional methodologies employed.

As technology and accessibility improvements are constantly emerging, we plan to update these guidelines periodically. 

See the following sections for more information:

* :ref:`Supporting Learners with Diverse Needs`
* :ref:`Accessibility Best Practices`
*
*


.. _Supporting Learners with Diverse Needs:

************************************************************
Supporting Learners with Diverse Needs
************************************************************

Almost one-fifth of the world's population has some kind of disability. 
Online courses can reduce many barriers to education for these learners by providing access to courses from any location, at any time, and through the use of assistive technologies.

EdX is dedicated to creating a platform that is not only itself accessible, but also enables course creators to create accessible content. 
If you encounter platform issues that you believe may affect your ability to provide accessible course content, please contact us at accessibility@edx.org. 
We also welcome your comments and questions.

In the following sections, we outline guidelines for creating and delivering course content that allows students to use built-in accessibility functionality (such as magnification and zoom features), assistive technologies, and alternative formats. 
These practices consider learners such as the following:

* Blind learners who use a screen reader, which reads page text aloud, or a Braille display device, which renders page text in Braille.

* Low-vision learners who use screen magnification software to enlarge text and other onscreen content.

* Learners with vision impairments, such as difficulty seeing in low-light conditions, who modify their browser or operating system to change background colors and text settings to make text easier to read.

* Learners with learning disabilities, such as dyslexia, who use text-to-speech technology that reads page content aloud.

* Physically disabled learners who use switching devices, voice recognition software, or eye-gaze activated technology instead of a standard mouse or keyboard to control their computer.

* Learners who modify their operating system settings to make the mouse or keyboard easier to use.

* Learners with hearing impairments who cannot access audio content and need the equivalent information in an alternative format, such as captions or a transcript.

We highly recommend that you implement the best practices shared with you in this document and other widely available resources (some of which are referred to herein). 
As mentioned above, if you cannot easily address these barriers, we recommend that you consult with any disability-related resources at your institution 
(Disability Services, Assistive Technology, or Accessibility). 
While your ability to support students in the MOOC context may be different from supporting on-campus students, 
we encourage you to develop a plan to respond to students who inform you of accessibility barriers to learning. 
However, given the large numbers of learners enrolling in many of the courses, you will quickly see how important it is to address accessibility concerns when creating a course.


.. _Accessibility Best Practices:

************************************************************
Accessibility Best Practices
************************************************************

* :ref:`Best Practices for Universal Design for Learning`
* :ref:`Best Practices for Readability`
* :ref:`Best Practices for Accessible PDFs`
* :ref:`Best Practices for Custom Content Types`


.. _Best Practices for Universal Design for Learning:

====================================================
Best Practices for Universal Design for Learning
====================================================

Universal Design for Learning focuses on delivering courses in a format so that as many of your learners as possible can 
successfully interact with the learning resources and activities you provide them, without compromising on pedagogic rigor and quality.

The principles of Universal Design for Learning can be summarized as:

#. Present information and content in different ways.
#. Differentiate the ways that students can express what they know.
#. Stimulate interest and motivation for learning.

Instructors can apply these principles in course design by:

* Designing resources and activities that can be accessed by learners in different ways 
  (for example, providing text that allows a student to enlarge it or change color, a diagram with an equivalent text description, or a video with audio and text captions).

* Providing multiple ways for learners to engage with information and demonstrate their knowledge. 
  This is particularly important when developing exercises and assessments.
  
* Identifying activities that require specific sensory or physical capability, such as activities that require color identification, 
  for which accommodating the specific accessibility needs of students will be difficult or impossible. 
  In these cases, consider whether there is a pedagogical justification for these requirements. 
  If there is a justification, consider communicating these requirements to prospective students in the course description and establish a 
  plan for responding to students who encounter barriers that can be addressed without fundamental alteration. 
  If there is no justification for the requirements, we recommend that you modify the learning activities to be more flexible and broadly accessible.
  
**Resources**

* Delivering Accessible Digital Learning (JISC Techdis) provides a useful overview of an inclusive approach to course design: 
  http://www.jisctechdis.ac.uk/techdis/resources/accessiblecontent

* The National Center on Universal Design for Learning provides a helpful overview on Universal Design for Learning: 
  http://www.udlcenter.org/implementation/postsecondary


.. _Best Practices for Readability:

====================================================
Best Practices for Readability
====================================================

EdX courses have a global and diverse audience. 
Learners will be better positioned to access the concepts of your content if it is written in clear, straightforward language and the content is well structured. 
Use appropriate terminology to your subject area, but keep it as clear and unambiguous as possible to help learners who:

* are not native English speakers; or
* have a disability that affects reading, such as dyslexia or a visual impairment.

To produce content that is more readable by all students:

* Make the names of elements such as course sections, subsections, units, components, and discussion topics descriptive 
  and easy to skim by putting the important information first in the name. 
  These names are used in navigation menus, page headings, and section headings and are signposts that help learners navigate your course and read course content. 
  “Front-loading” menus and headings particularly helps screen reader users, who can more quickly assess the relevance of a link or heading.

* When creating written learning resources, break text into sections by using HTML elements, such as headings, paragraphs, and lists. 
  Long blocks of unbroken text are a barrier to most readers. Segmented content is more inviting and is easier to navigate and search. 
  See “Best Practices for HTML Markup,” below, for guidance on creating accessible HTML.

* Avoid jargon. If unfamiliar words or phrases are relevant to the subject, explain them when they are first used, and include a glossary with your course materials. 
  When using an abbreviation or acronym, write out the phrase the first time it appears: for example, “National Aeronautics and Space Administration (NASA).”

* Use link text that clearly explains the link destination (for example, “Review the Course Syllabus”). 
  Avoid using constructs like “You can review the Course Syllabus here.” For links that point to documents rather than web pages, 
  include the document type in the link (e.g., “Course Syllabus (PDF)”).

**Resources**

* The Center for Plain Language provides detailed resources on writing clearly and concisely, in language appropriate for your content and target audience: 
  http://centerforplainlanguage.org/about-plain-language/checklist/

.. _Best Practices for Accessible PDFs:

====================================================
Best Practices for Accessible PDFs
====================================================

PDF is a common format for course materials, including textbooks supplied by publishers. 
However, converting materials to PDFs can create accessibility barriers, particularly for learners with visual impairments. 
To improve the accessibility of your PDFs, review the guidance below about preparing documents for conversion, using Adobe Acrobat Professional, 
and working with third-party suppliers.

+++++++++++++++++++++++++++++++++++++++++++++
Converting Microsoft Office documents to PDF
+++++++++++++++++++++++++++++++++++++++++++++
The teaching materials that you will convert to PDFs may use different formats—for example, your syllabus may be in Word, 
your presentation slides in PowerPoint, and your textbooks in publisher-supplied PDF. 
Use the tools available in the applicable software to create well-structured source documents. 
This early step helps minimize issues that may be difficult or impossible to address later in the conversion process.

**Preparing Word documents**

* Keep formatting simple. Use headings, paragraphs, lists, images, and captions, and tables for tabular data. 
  Don’t add unnecessary indents, rules, columns, blank lines, and typographic variation. The simpler the formatting, the easier it will be to make an accessible PDF document.

* Use styles for formatting your text, such as Normal, Heading 1, and Heading 2, rather than manually formatting text using bold and indents. 
  Add alternative text to images (see “Best Practices for Describing Images,” below) using Word’s picture formatting options.

**Preparing PowerPoint documents**

* To help make your content accessible and comprehensible to learners who use screen reading software, start in Outline view and include all of your content as text. 
  Add design elements and images after completing the outline, and use PowerPoint’s picture formatting options to include detailed descriptions of images that convey information. Avoid adding animations or transitions, as they will not be saved with the PDF format.

* Use the Home > Drawing > Arrange > Selection Pane option to view the reading order of objects on each slide. If the reading order is not logical, reorder the objects.

* Use the Home > Slides > Reset option to give each slide a unique and informative title. The title can be hidden if preferred.

* Identify column headers for any data table using PowerPoint’s table formatting options (Tables > Table Options > Header Row), 
  and ensure that each header contains informative text describing the data in that column.

**Preparing Excel spreadsheets**

* Use a unique and informative title for each worksheet tab.

* Include text alternatives for images (see “Best Practices for Describing Images,” below) using Excel’s picture formatting options.

* Identify column headers using Excel’s table formatting options (Table > Table Options > Header Row), and include in each header cell informative text describing the data in that column.

* Do not use blank cells for formatting.

* Use descriptive link text rather than URLs in data cells.

**Converting Word, PowerPoint, and Excel documents to PDF**

To generate PDFs from Microsoft Office documents, use the **Save as PDF** option. 
Make sure the **Document Structure Tags for Accessibility** option is selected (consult your software documentation for more details). 
Note that PDFs generated from Windows versions of Office will be more accessible than those generated from Mac OS.

+++++++++++++++++++++++++++++++++++++++++++++
Working with third-party supplied PDFs
+++++++++++++++++++++++++++++++++++++++++++++

When you control the creation of a PDF, you have greater control over the document’s accessibility. 
If you use PDFs provided by third parties, including textbooks supplied by publishers, the document’s accessibility may be unknown.

**Asking the right questions about accessible PDFs**

Where possible, ask the supplier of the PDF if the PDF is accessible. If it isn’t, ask whether the supplier can provide an accessible version. Questions to ask include:

* Can screen readers read the document text?
* Do images in the document include text descriptions?
* Are all tables, charts, and math provided in an accessible format?
* Does all media include text equivalents?
* Does the document have navigational aids, such as a table of contents, index, headings, and bookmarks?

+++++++++++++++++++++++++++++++++++++++++++++
Updating PDFs for accessibility
+++++++++++++++++++++++++++++++++++++++++++++

You may need to update your existing teaching materials in PDF format to improve accessibility. This might include PDFs that were:

* created by scanning a hard-copy document;
* generated from a document that was not created with accessibility in mind; or
* generated by a process that does not preserve source accessibility information.

In such cases, you need special software, such as Adobe Acrobat Professional, to enhance the accessibility of the PDF. 
PDFs that are created from scanned documents require a preliminary Optical Character Recognition (OCR) step to generate a text version of the document. 
The procedure checks documents for accessibility barriers, adds properties and tags for document structure, sets the document’s language, and adds alternative text for images.

**Resources**

* Microsoft provides detailed guidance on generating accessible PDFs from Microsoft Office applications, including Word, Excel, and PowerPoint:
  http://office.microsoft.com/en-gb/word-help/create-accessible-pdfs-HA102478227.aspx

* Adobe provides a detailed accessibility PDF repair workflow using Acrobat XI: 
  http://www.adobe.com/content/dam/Adobe/en/accessibility/products/acroba t/pdfs/acrobat-xi-pdf-accessibility-repair-workflow.pdf

* Adobe Accessibility (Adobe) is a comprehensive collection of resources on PDF authoring and repair, using Adobe’s products: 
  http://www.adobe.com/accessibility.html

* PDF Accessibility (University of Washington) provides a step-by-step guide to creating accessible PDFs from different sources and using different applications: 
  http://www.washington.edu/accessibility/pdf/

* PDF Accessibility (WebAIM) provides a detailed and illustrated guide on creating accessible PDFs: 
  http://webaim.org/techniques/acrobat/

* The National Center of Disability and Access to Education has a collection of one- page “cheat sheets” on accessible document authoring: 
  http://ncdae.org/resources/cheatsheets/

* The Accessible Digital Office Document (ADOD) Project provides guidance on creating accessible Office documents: 
  http://adod.idrc.ocad.ca/

.. _Best Practices for Custom Content Types:

====================================================
Best Practices for Custom Content Types
====================================================
Using different content types can significantly add to the learning experience. 
We discuss below how to design several custom content types to be accessible to students with disabilities.

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Information graphics (charts, diagrams, illustrations)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Although images can be helpful for communicating concepts and information, they present challenges for people with visual impairments. 
For example, a chart that requires color perception or a diagram with tiny labels and annotations will likely be difficult to comprehend for learners with color blindness or low vision. 
All images present a barrier to learners who are blind.

The following are best practices for making information graphics accessible to visually impaired students:

* Avoid using only color to distinguish important features of the image. For example, on a line graph, use a different symbol as well as color to distinguish the data elements.
* Whenever possible, use an image format, such as SVG, that supports scaling. Consider providing a high-resolution version of complex graphics that have small but essential details.
* Provide a text alternative that describes the information in the graphic. For charts and graphs, a text alternative could be a table displaying the same data. 
  See “Best Practices for Describing Images,” below, for details about providing text alternatives for images.

++++++++++++++++++++++++++++++++++++++++++++
Math content
++++++++++++++++++++++++++++++++++++++++++++

Math in online courses has been challenging to deliver in a way that is accessible to people with vision impairments. 
Instructors frequently create images of equations rather than including text equations. 
Math images cannot be modified by people who need a high-contrast display and cannot be read by screen reader software.
EdX uses MathJax to render math content in a format that is clear, readable, and accessible to people who use screen readers. 
MathJax works together with math notation, like LaTeX and MathML, to render mathematical equations as text instead of images. 
We recommend that you use MathJax to display your math content. 
You can learn more about using MathJax in the edX101 course, the Studio support documentation and in the MathJax documentation on accessibility (see the link in “Resources” below). 
We will update these guidelines as improvements to MathJax are developed.

++++++++++++++++++++++++++++++++++++++++++++
Simulations and interactive modules
++++++++++++++++++++++++++++++++++++++++++++

Simulations, including animated or gamified content, can enhance the learning experience. 
In particular, they benefit learners who may have difficulty acquiring knowledge from reading and processing textual content alone. 
However, simulations can also present some groups of learners with difficulties. 
To minimize barriers, consider the intended learning outcome of the simulation. 
Is it to reinforce understanding that can also come from textual content or a video lecture, or is it to convey new knowledge that other course resources can’t cover? 
Providing alternative resources will help mitigate the impact of any barriers.

Although you can design simulations to avoid many accessibility barriers, some barriers, particularly in simulations supplied by third parties, 
may be difficult or impossible to address for technical or pedagogic reasons. 
Understanding the nature of these barriers can help you provide workarounds for learners who are affected. 
Keep in mind that attempted workarounds for simulations supplied by third parties may require the supplier’s consent if copyrighted material is involved.

Consider the following questions when creating simulations, keeping in mind that as the course instructor, 
you enjoy considerable freedom in selecting course objectives and outcomes. 
Additionally, if the visual components of a simulation are so central to your course design, 
providing alternate text description and other accommodations may not be practical or feasible:

* Does the simulation require vision to understand? If so, provide text describing the concepts that the simulation conveys.
* Is the mouse necessary to operate the simulation? If so, provide text describing the concepts that the simulation conveys.
* Does the simulation include flashing or flickering content that could trigger seizures? If so and this content is critical to the nature of the simulation:
 
  * do not require learners to use the simulation for a required assessment
    activity; and
  * provide a warning that the simulation contains flickering or flashing content.

As best practices continue to emerge in this area, we will update these guidelines.

++++++++++++++++++++++++++++++++++++++++++++
Online exercises and assessments
++++++++++++++++++++++++++++++++++++++++++++

For activities and assessments, consider difficulties students may have in completing an activity and consider using multiple assessment options, 
keeping in mind that some of the end users have disabilities. 
Focus on activities that allow students to complete the activity and submit their work without difficulties.

Some students take longer to read information and input responses, such as students with visual or mobility impairments and students who need time to comprehend the information. 
If an exercise has a time limit, consider whether it’s long enough to allow students to respond. Advanced planning may help cut down on the number of students requesting 
time extensions.

Some online exercise question types may be difficult for students who have vision or mobility impairments. For example:

* Exercises requiring fine hand-eye coordination, such as image mapped input or drag and drop exercises, 
  may present difficulties to students who have limited mobility. Consider alternatives that do not require fine motor skills, unless, of course, 
  such skills are necessary for effective participation in the course. For example, for a drag-and-drop exercise mapping atoms to compounds, provide a
  checkbox or multiple-choice exercise.

* Highly visual stimuli, such as word clouds, may not be accessible to students
  who have visual impairments. Provide a text alternative that conveys the same information, such as an ordered list of words in the word cloud.

++++++++++++++++++++++++++++++++++++++++++++    
Third-party content
++++++++++++++++++++++++++++++++++++++++++++

When including links to third-party content in your course, be mindful as to the accessibility of such third party resources, 
which may not be readily accessible to learners with disabilities. We recommend that you test any links prior to sharing them with users.

You can use the eReader tool or the “Files and Uploads” option in edX Studio to incorporate third-party textbooks and other 
publications in PDF format into your course. You can also incorporate such materials into your course in HTML format. 
See “Best Practices for Accessible PDFs,” above, for guidance on working with third- party supplied PDFs, and “Best Practices for HTML Markup,” below, 
for guidance on creating accessible HTML.


**Resources**

* Effective Practices for Description of Science Content within Digital Talking Books, from the National Center for Accessible Media, provides best practices for describing graphs, 
  charts, diagrams, and illustrations: 
  http://ncam.wgbh.org/experience_learn/educational_media/stemdx

* The University of Washington’s DO-IT project provides guidance on creating accessible math content: 
  http://www.washington.edu/doit/Faculty/articles?465

* AccessSTEM provides guidance on creating accessible science, technology, engineering and math educational content: 
  http://www.washington.edu/doit/Stem/

* The National Center on Educational Outcomes (NCEO) provides Principles and Characteristics of Inclusive Assessment and Accountability Systems: 
  http://www.cehd.umn.edu/nceo/onlinepubs/Synthesis40.html

* MathJax provides guidance on creating accessible pages with the display engine: 
  http://www.mathjax.org/resources/articles-and-presentations/accessible- pages-with-mathjax/