=====================================
Processing Scheduled Instructor Tasks
=====================================

Status
------

Accepted

Background
----------
The previous ADR (``Scheduled Instructor Tasks``) explains the motivation and approach for scheduling instructor tasks.

This ADR will cover our approach for the execution of scheduled instructor tasks.

Decision
--------

A management command will be introduced to assist in processing scheduled instructor tasks. This management command will rely on new utility functions in the **instructor_task** app of edx-platform to query tasks that have the **SCHEDULED** status and then determine if these tasks are due for execution.

This management command will be invoked by a Jenkins job running on a (cron) schedule to process scheduled tasks due for execution.	The job will run every fifteen minutes.

Rejected Solutions
------------------

Celery Beat
===========

`Celery Beat`_ is a scheduler for periodic tasks. When seeking feedback on using Celery Beat for this project we were warned to stay away. We are under the impression that there have been several attempts to utilize Celery Beat in edx-platform over the past few years that haven't been successful. For this reason we have decided not to explore its use.

.. _Celery Beat: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#introduction