.. include:: ../links.rst

.. _Installing the edX Developer Stack:

####################################
Installing the edX Developer Stack
####################################

This chapter is intended for those who are installing and running the edX Developer Stack.

See the following sections:

* `Overview`_
* `Components`_
* `Knowledge Prerequisites`_
* `Software Prerequisites`_
* `Install DevStack`_
* `Install DevStack using the Torrent file`_


**********
Overview
**********

The edX Developer Stack, known as **Devstack**, is a Vagrant instance designed
for local development.

Devstack:

* Uses the same system requirements as production. This allows you to
  discover and fix system configuration issues early in development.

* Simplifies certain production settings to make development more convenient.
  For example, `nginx`_ and `gunicorn`_ are disabled in Devstack; Devstack uses
  Django's runserver instead.

See the `Vagrant documentation`_ for more information.

********************
Components
********************

Devstack includes the following edX components:

* The Learning Management System (LMS)
* edX Studio
* Discussion Forums
* Open Response Assessor (ORA)
  
Devstack also includes a demo edX course.

**************************
Knowledge Prerequisites
**************************

To use Devstack, you should:

* Understand basic terminal usage. If you are using a Mac computer, see
  `Introduction to the Mac OS X Command Line`_. If you are using a Windows
  computer, see `Windows Command Line Reference`_.

* Understand Vagrant commands. See the `Vagrant Getting Started`_ guide for more
  information.


**************************
Software Prerequisites
**************************

To install and run Devstack, you must first install:

* `VirtualBox`_ 4.3.10 or higher

* `Vagrant`_ 1.5.3 or higher

* An NFS client, if your operating system does not include one. Devstack uses
  VirtualBox Guest Editions to share folders through NFS.
  

**************************
Install DevStack
**************************

To install Devstack directly from the command line, follow the instructions
below. You can also install DevStack using a Torrent file, as explained in the
next section.

Before beginning the installation, ensure that you have your local computer's administrator's password.

#. Ensure the ``nfsd`` client is running.

#. Create the ``devstack`` directory and navigate to it in the command prompt.
   
   .. code-block:: bash

     mkdir devstack
     cd devstack

#. Download the Devstack Vagrant file.
   
   .. code-block:: bash

     curl -L https://raw.github.com/edx/configuration/master/vagrant/release/devstack/Vagrantfile > Vagrantfile

#. Install the Vagrant vbguest plugin.
   
   .. code-block:: bash

     vagrant plugin install vagrant-vbguest

#. Create the Devstack virtual machine.

   .. code-block:: bash

     vagrant up

   The first time you create the Devstack virtual machine, Vagrant downloads the
   base box, which is about 4GB. If you destroy and recreate the virtual
   machine, Vagrant re-uses the box it downloaded. See `Vagrant's documentation on boxes`_ for more information.

#. When prompted, enter your local computer's administrator's password.
   
   Your password is needed so that NFS can be set up to allow users to access
   code directories directly from your computer.

When you have completed these steps, see :ref:`Running the edX Developer Stack`
to begin using Devstack.


*****************************************
Install Devstack using the Torrent file
*****************************************

#. Download the Devstack `Torrent`_ file. 

#. When you have the file on your computer, add the Virtual machine using the
   command:

    .. code-block:: bash
  
     vagrant box add box-name path-to-box-file
