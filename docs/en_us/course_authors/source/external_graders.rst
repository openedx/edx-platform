.. _Using External Graders:

###########################
Using External Graders
###########################
This chapter describes how external graders work, how to set up problems to use external graders, and operational issues you must address.

*
*
*


.. _External Grader Overview:
*******************
Overview
*******************

An external grader is a system you deploy separately from the edX platform that receives student resposnes to a problem, processes those responses, and returns feedback and a problem grade to the edX platform.

Using an external grader is particularly useful for software programming courses where students are asked to submit complicated code.  The external grader can run tests that you define on that code and return results to a student.

For example, the student enters Python code for the following problem.  When the student clicks Check, the code is sent to an external grader, where tests are run on it.  If the code passes all tests, the external grader returns the score you assigned to the problem and a notice that the solution is correct.

.. image:: Images/external-grader-correct.png
 :alt: Image of a students view of a programming problem that uses an external grader, with a correct result 


The external grader can return a string with results, which can be displayed to the student. This can be particularly useful when the solution is not correct and you want to return information about the failed tests. For example:

.. image:: Images/external-grader-incorrect.png
 :alt: Image of a students view of a programming problem that uses an external grader, with a correct result 


**************************************
External Graders and XQueue
**************************************

To use an external grader to check problems, you use an XQueue server.  XQueue is the edX interface that manages communication between the edX Platform and your external grader.  The XQueue provides student input to the external grader; it then receives results from the external grader and returns them to the student using the edX Learning Management System.  

XQueue must be set up in one of two modes:

*  **Pull**


*  **Push**


You must determine which mode to use when you are building your course and your external grader, and communicate this decision to your edX Program Manager.

[DO WE NEED TO MORE SPECIFICALLY DEFINE THE RESTful INTERFACE FOR THIS?]

==================
Pull Mode
==================

In Pull mode, student submissions are collected in XQueue, where they remain until the external grader actively retrieves, or pulls, the next submission from the queue for grading.

The external grader polls the XQueue through a RESTful interface at a regular interval. When the external grader receives a submission, it runs the defined tests on it, then pushes the response back to XQueue through the RESTful interface. XQueue then delivers the response to the edX Learning Management System.


==================
Push Mode
==================

In Push mode, XQueue actively pushes student submissions to the external grader, which passivily waits for the next submission to grade. When the external grader receives a submission, it runs the defines tests on it, then synchronously delivers the graded response back to the XQueue. XQueue then delivers the response to the edX Learning Management System.



============================
External Grader Workflow
============================

The following steps show the complete process:

#. The student either enters code or attaches a file for a problem, then clicks Check.
#. XQueue either pushes the code to the external grader, or waits until the external grader pulls the code.
#. The external runs tests that you define on the code.
#. The external grader returns the the XQueue the grade for the code, as well as any results in a string. 
#. The XQueue delivers the results to the edX Learning Management System.
#. The student sees the problem results and the grade.


****************************
Building an External Grader
****************************

Course staff, not edX, is responsible for building and deploying the external grader. 

In addition to creating tests that are specific to the problems you add to your course, there are four areas that you must plan for when building an external grader:

* **Scale**
* **Security**
* **Reliability**
* **Notifications**

==================
Scale
==================

Your external grader must be able to scale to support the number of students in your course.

Keep in mind that student submissions will likely come in spikes, and not in an even flow.  For example, you should expect the load to be much greater than average in the hours before an exam is due.  Therefore, you should verify that the external grader can process submissions from a majority of students in a short period of time. [HOW MUCH MORE SPECIFIC CAN WE BE HERE]

==================
Security
==================

Students are submitting code than executes directly on a server your are responsible for. It is possible that a student submits malicious code to your external grader. Your system must protect against this and ensure that it runs only code that is relevent to the course problems.  How you implement these protections depends on the programming language you are using and your deployment architecture.  You should verify that your external grader can identify malicious code and prevent its execution.

==============================
Reliability and Recovery
==============================

Once your course starts, many students will submit code at any possible time, and expect to see results quickly.  If your external grader is prone to failure or unexpected delays, the student experience will be poor.

Therefore, you must ensure that your external grader has high availability and can recover from errors.   Prior to your course starting, you must develop a plan to immediately notifiy the team reponsible for operating your external grader, as well as edX operations, when the external grader fails. Contact your edX Program Manager for more information.

If you know the external grader will be unavailable at a certain time for maintenance, you should :ref:`Add a Course Update`. 

==================
Notifications
==================

***************************
Set up an External Grader
***************************

1.  Request new xqueue from PM and get name

2. Set up problems -- example of text box and upload file

3. Set up graders.  hosting responsibility.

4. test (and negative test) your problems.



