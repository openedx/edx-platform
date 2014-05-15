***********************************
So You Want to Deploy a New Service
***********************************

Intro
=====

This page is a work-in-progress aimed at capturing all the details needed to
deploy a new service in the edX environment.

Considerations
==============

What Does Your Service Do
-------------------------
Understanding how your service works and what it does helps Ops support
the service in production.

Sizing and Resource Profile
---------------------------
What class of machine does your service require.  What resources are most
likely to be bottlenecks for your service, CPU, memory, bandwidth, something else?

Customers
---------
Who will be consuming your service?  What is the anticipated initial usage?
What factors will cause usage to grow?  How many users can your service support?

Code
----
What repository or repositories does your service require.
Will your service be deployed from a non-public repo?

Ideally your service should follow the same release management process as the LMS.
This is documented in the wiki, so please ensure you understand that process in depth.

Was the service code reviewed?

Settings
--------
How does your service read in environment specific settings?  Were all
hard-coded references to values that should be settings, e.g., database URLs
and credentials, message queue endpoints, etc.,  found and resolved during
code review?

License
-------
Is the license included in the repo?

How does your service run
-------------------------
Is it HTTP based?  Does it run periodically?  Both?

Persistence
-----------
Ops will need to know the following things:

* What persistence needs does you service have

  * Will it connect to an existing database?
  * Will it connect to Mongo

* What are the least permissive permissions your service needs to do its job.

Logging
-------

It's important that your application logging in built out to provide sufficient
feedback for problem determination as well as ensuring that it is operating as
desired.  It's also important that your service log using our deployment
standards, i.e., logs vi syslog in deployment environments and utilizes the
standard log format for syslog.  Can the logs be consumed by Splunk?  They
should not be if they contain  data discussed in the Data Security section below.

Metrics
-------
What are the key metrics for your application?  Concurrent users?
Transactions per second?  Ideally you should create a DataDog view that
captures the key metrics for your service and provided an instant gauge of
overally service health.

Messaging
---------
Does your service need to access a message queue.

Email
-----
Does your service need to send email

Access to Other Service
-----------------------
Does your service need access to other service either within or
outside of the edX environment.  Some example might be, the comment service,
the LMS, YouTube, s3 buckets, etc.

Service Monitoring
------------------
Your service should have a facility for remote monitoring that has the
following characteristics:

* It should exercise all the components that your service requires to run successfully.
* It should be necessary and sufficient for ensuring your service is healthy.
* It should be secure.
* It should not open your service to DDOS attacks.

Fault Tolerance and Scalability
-------------------------------
How can your application be deployed to ensure that it is fault tolerant
and scalable?

Network Access
--------------
From where should your service be accessible.

Data Security
-------------
Will your application be storing or handling data in any of the
following categories:

* Personally Identifiable Information in General, e.g., user's email addresses.
* Tracking log data
* edX confidential data

Testing
-------
Has your service been load tested?  What there the details of the test.
What determinations can we make regarding when we will need to scale if usage
trend upward?  How can ops exercise your service in order to tests end-to-end
integration.  We love no-op-able tasks.

Additional Requirements
-----------------------
Anything else we should know about.
