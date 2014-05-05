.. _Adding Pages to a Course:

###########################
Adding Pages to a Course
###########################


*******************
Overview
*******************

By default, your course has the following pages:

* Courseware
* Course Info
* Discussion
* Wiki
* Progress

You cannot rename, reorder, or remove these pages.

You can add pages to your course. Each page appears in your course's navigation bar. 

For example, the following navigation bar includes the default pages as well as the
**Course Schedule** and **Supplements & Instructor's Blog** pages.

.. image:: ../Images/page_bar_lms.png
 :alt: Image of the page bar in the LMS

You can create other pages for the grading policy, course slides, or any other purpose. More examples of pages you can add are:

* A Google calendar, by embedding the code for it.  

* A dynamic HTML calendar, using the template in :ref:`Code for Dynamic HTML Schedule`.

* An instant hangout.  See :ref:`Google Instant Hangout` for more information.

See:

* :ref:`Add a Page`
* :ref:`Show or Hide the Course Wiki Page`
* :ref:`Reorder Pages`
* :ref:`Delete a Page`
* :ref:`Code for Dynamic HTML Schedule`


.. _`Add a Page`:

****************
Add a Page
****************

#. In Studio, from the **Content** menu, select **Pages**. 

  .. image:: ../Images/pages_page.png
   :alt: Image of the Pages screen


2. Click **Add a New Page**. A page with the title **Empty** is added to the list:

  .. image:: ../Images/pages_empty.png
   :alt: Image of the Pages screen with a new Empty page

3. Click **Edit**. The HTML editor opens.  

  .. image:: ../Images/pages_editor.png
   :alt: Image of the Page editor

4. Enter text for your page. See :ref:`Options for Editing HTML Components` for more information about using the editor.
#. Click **Settings** to edit the **Display Name**. The display name is the name of the page visible to students in the course.
#. Click **Save**. 

The new page is immediately available to students, if the course has started.

.. _Show or Hide the Course Wiki Page:

************************************************
Show or Hide the Course Wiki Page
************************************************

By default, your course includes a Wiki page. Students and course staff can use the Wiki to post content and comment on others' content.

If you do not want to use the Wiki in your course, you can hide the page.

The eye icon in the Wiki object indicates that the Wiki page is visible in your course:

.. image:: ../Images/pages_wiki_on.png
 :alt: Image of the Pages page with the Wiki made visible

Click the eye icon to hide the Wiki page. The icon changes:

.. image:: ../Images/pages_wiki_off.png
 :alt: Image of the Pages page with the Wiki made visible

Click it again to make the Wiki page visible.

.. note:: Content remains in the Wiki when you hide the page. For example, if a student bookmarks a Wiki topic, then you hide the Wiki page, the student can still use the bookmark to access that Wiki topic. All content that was previously posted in the Wiki remains available after you hide the Wiki page, and any students logged in to edX can access the content if they know the URL. 

.. _Reorder Pages:

****************
Reorder Pages
****************

You can reorder pages in your course by dragging and dropping the pages to different locations. 

To move a page, hover over the element handle on the right side of the page row until the mouse pointer changes to a four-headed arrow. Then, click and drag the page to the location that you want.

.. note:: You cannot reorder the Courseware, Course Info, Discussion, Wiki, and Progress pages that your course includes by default

.. _Delete a Page:

****************
Delete a Page
****************

To delete a page that you previously added, click the trash can icon in the row for the page.  You are prompted to confirm the deletion.

.. _Code for Dynamic HTML Schedule:

********************************
Code for Dynamic HTML Schedule
********************************

You can use the following code in a page to provide a dynamic HTML schedule in your course.

.. code-block:: html


	<div class= "syllabus">

	<table style="width: 100%">
 		<col width="10%">
 		<col width="15%">
  		<col width="10%">
  		<col width="30%">
  		<col width="10%">
  		<col width="15%">
  		<col width="10%">
  
	<!-- Headings -->
 		 <thead>
    			<td class="day"> Wk of </td>
   			<td class="topic"> Topic </td>
   			<td class="reading"> Read </td>
    			<td class="video"> Lecture Sequence </td>	
    			<td class="slides"> Slides </td>
    			<td class="assignment"> HW/Q </td>
			<td class="due"> Due </td>
  		</thead>
  
	<!-- Week 1 Row 1 -->
 		 <tr class="first">
   			<td class="day">10/22</td>
			<td class="topic">Topic 1</td>
			<td class="reading">Ch. 1</td>
    			<td class="video"><a href="#">L1: Title</a></td>
    			<td class="slides"><a href="#">L1</a></td>
    			<td class="assignment"><a href="#">HW 1</a></td>
    			<td class="due">11/04</td>
  		</tr>
  
	<!-- Week 1 Row 2 -->
    		<tr>
    			<td class="day"> </td>
    			<td class="topic"></td>
    			<td class="reading"></td>
    			<td class="video"><a href="#">L2: Title</a></td>
    			<td class="slides"><a href="#">L2</a></td>
    			<td class="assignment">     </td>
   			 <td class="due">      </td>
  		</tr>

   		 <tr> <td class="week_separator" colspan=7> <hr/> </td> </tr>
  
	<!-- Week 2 Row 1 -->
 		 <tr>
    			<td class="day">10/29</td>
    			<td class="topic">Topic 2</td>
    			<td class="reading">Ch. 2</td>
    			<td class="video"> <a href="#">L3: Title<a></td>
   			 <td class="slides"><a href="#">L3</a></td>
    			<td class="assignment"><a href="#">Quiz 1</a></td>
    			<td class="due">11/11</td>
 		 </tr>
  
	<!-- Week 2 Row 2 -->
 		<tr>
  			<td class="day"></td>
    			<td class="topic"></td>
    			<td class="reading"></td>
    			<td class="video"><a href="#">L4: Title</a></td>
    			<td class="slides"><a href="#">L4</a> </td>
    			<td class="assignment"></td>
    			<td class="due"></td>
  		</tr>
  		<tr> <td class="week_separator" colspan=7> <hr/> </td> </tr>
  
	<!-- Week 3 Row 1 -->
  		<tr>
    			<td class="day">11/05</td>
    			<td class="topic">Topic 3</td>
    			<td class="reading">Ch. 3</td>
    			<td class="video"><a href="#">L5: Title</a></td>
    			<td class="slides"><a href="#">L5 </a></td>
    			<td class="assignment"><a href="#">HW 2</a></td>
    			<td class="due">11/18 </td>
  		</tr>
  
	<!-- Week 3 Row 2 -->
		<tr>
    			<td class="day"> </td>
    			<td class="topic"> </td>
    			<td class="reading"></td>
    			<td class="video"><a href="#">L6: Title</a></td>
    			<td class="slides"><a href="#">L6 </a></td>
    			<td class="video"></td>
    			<td class="assignment"></td>
    			<td class="due"></td>
  		</tr>
  		<tr> <td class="week_separator" colspan=7> <hr/> </td> </tr>
  
	<!-- Week 4 Row 1 -->
  		<tr>
    			<td class="day">11/12</td>
    			<td class="topic">Topic 4</td>
    			<td class="reading">Ch. 4</td>
    			<td class="video"><!--<a href="#">L7: Title</a>--> L7: Title</td>
    			<td class="slides"><!--<a href="#">L7</a>-->L7</td>
    			<td class="assignment"><!--<a href="#">Quiz 2</a>-->Quiz 2</td>
    			<td class="due"> 11/25 </td>
  		</tr>
  
	<!-- Week 4 Row 2 -->
    		<tr>
    			<td class="day"></td>
    			<td class="topic"></td>
    			<td class="reading"></td>
    			<td class="video"><!--<a href="#">L8: Title</a>-->L8: Title</td>
    			<td class="slides"><!--<a href="#">L8</a>-->L8</td>
    			<td class="assignment"></td>
    			<td class="due"></td>
  		</tr>
  		<tr> <td class="week_separator" colspan=7> <hr/> </td> </tr>
  
	<!-- Week 5 Row 1 -->
  		<tr>
    			<td class="day">11/19</td>
    			<td class="topic">Topic 5</td>
    			<td class="reading">Ch. 5</td>
    			<td class="video"><!--<a href="#">L9: Title</a>-->L9: Title</td>
    			<td class="slides"><!--<a href="#">L9</a>-->L9</td>
    <			td class="assignment"><!--<a href="#">HW 3</a>-->HW 3</td>
    			<td class="due"> 12/02 </td>
  		</tr>
  
	<!-- Week 5 Row 2 -->
   		<tr>
    			<td class="day"></td>
    			<td class="topic"></td>
    			<td class="reading"></td>
    			<td class="video"><!--<a href="#">L10: Title</a>-->L10: Title</td>
    			<td class="slides"><!--<a href="#">L10</a>-->L10 </td>
    			<td class="assignment"></td>
    			<td class="due"></td>
  		</tr>
  		<tr> <td class="week_separator" colspan=7> <hr/> </td> </tr>
  
	<!-- Week 6 Row 1 -->
  		<tr>
    			<td class="day">11/26</td>
    			<td class="topic">Topic 6</td>
    			<td class="reading">Ch. 6</td>
    			<td class="video"><!--<a href="#"><L11: Title</a>-->L11: Title </td>
    			<td class="slides"><!--<a href="#">L11</a>-->L11</td>
    			<td class="assignment"><!--<a href="#">HW 4</a>-->HW 4</td>
    			<td class="due">12/09</td>
  		</tr>
  
	<!-- Week 6 Row 2 -->
    		<tr>
			<td class="day"> </td>
    			<td class="topic"> </td>
    			<td class="reading"></td>
    			<td class="video"><!--<a href="#">L12: Title</a>-->L12: Title</td>
    			<td class="slides"><!--<a href="#">L12</a>-->L12</td>
    			<td class="assignment"></td>
    			<td class="due">      </td>
		</tr>

	</table>
	</div>

