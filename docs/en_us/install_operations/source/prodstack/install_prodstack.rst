.. include:: ../links.rst

.. _Installing the edX Production Stack:

####################################
Installing the edX Production Stack
####################################

This chapter is intended for those who are installing and running the edX Production Stack.

See the following sections:

* `Overview`_
* `Components`_
* `Knowledge Prerequisites`_
* `Software Prerequisites`_
* `Install the edX Production Stack`_


**********
Overview
**********

The edX Production Stack, known as **Fullstack**, is a Vagrant instance designed
for deploying all edX services on a single server.

See the `Vagrant documentation`_ for more information.


********************
Components
********************

Fullstack includes the following edX components:

* The Learning Management System (LMS)
* edX Studio
* XQueue, the queuing server that uses `RabbitMQ`_ for external graders
* Discussion Forums
* Open Response Assessor (ORA)
* `Discern`_, the machine-learning-based automated textual classification API
  service.
* `Ease`_, a library for the classification of textual content.
  

**************************
Knowledge Prerequisites
**************************

To use Fullstack, you should:

* Understand basic terminal usage. If you are using a Mac computer, see
  `Introduction to the Mac OS X Command Line`_. If you are using a Windows
  computer, see `Windows Command Line Reference`_.

* Understand Vagrant commands. See the `Vagrant Getting Started`_ guide for more
  information.


**************************
Software Prerequisites
**************************

To install and run Fullstack, you must first install:

* `VirtualBox`_ 4.3.10 or higher

* `Vagrant`_ 1.5.3 or higher

* An NFS client, if your operating system does not include one. Fullstack uses
  `VirtualBox Guest Editions`_ to share folders through NFS.
  

*********************************
Install the edX Production Stack
*********************************

To install Fullstack directly from the command line, follow the instructions
below.

Before beginning the installation, ensure that you have your local computer's administrator's password.

#. Ensure the ``nfsd`` client is running.

#. Create the ``fullstack`` directory and navigate to it in the command prompt.
   
   .. code-block:: bash

     mkdir fullstack
     cd fullstack

#. Download the fullstack Vagrant file.
   
   .. code-block:: bash

     curl -L https://raw.githubusercontent.com/edx/configuration/master/vagrant/release/fullstack/Vagrantfile > Vagrantfile

#. Install the Vagrant hostsupdater plugin.
   
   .. code-block:: bash

     vagrant plugin install vagrant-hostsupdater

#. Create the Fullstack virtual machine.

   .. code-block:: bash

     vagrant up

   The first time you create the Fullstack virtual machine, Vagrant downloads the
   base box, which is about 4GB. If you destroy and recreate the virtual
   machine, Vagrant re-uses the box it downloaded. See `Vagrant's documentation on boxes`_ for more information.

#. When prompted, enter your local computer's administrator's password.
   
   Your password is needed so that NFS can be set up to allow users to access
   code directories directly from your computer.

**********************************************
Browser Login To Your New edX Production Stack
**********************************************

#. Go to preview.localhost in your browser, which is an alias entry for 192.168.33.10 that was created in your /etc/hosts file.

   When prompted, enter **edx** for both username and password.
