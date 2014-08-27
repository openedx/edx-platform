.. include:: ../links.rst

.. _Running the edX Developer Stack:

####################################
Running the edX Developer Stack
####################################

See the following sections:

* `Connect to the Devstack Virtual Machine`_
* `Set Up Ability to Preview Units (Mac/Linux Only)`_
* `Customize the Source Code Location`_
* `Run the LMS on Devstack`_
* `Run Studio on Devstack`_
* `Run Discussion Forums on Devstack`_
* `Default Accounts on Devstack`_


****************************************
Connect to the Devstack Virtual Machine
****************************************

#. To connect to the Devstack virtual machine, use the SSH command from the
   `devstack` directory.

  .. code-block:: bash

   vagrant ssh

2. To use Devstack and perform any of the tasks described in this section, you
   must connect as the user **edxapp**.

   .. code-block:: bash

    sudo su edxapp

   This command loads the edxapp environment from the file
   ``/edx/app/edxapp/edxapp_env``. This puts ``venv python`` and ``rbenv ruby``
   in your search path.

   This command also sets the current working directory to the edx-platform
   repository (``/edx/app/edxapp/edx-platform``).


****************************************************
Set Up Ability to Preview Units (Mac/Linux Only)
****************************************************

If you are installing Devstack on a Linux or Macintosh computer, in order to use
the preview feature in edX Studio, you must add the following line to the
``etc/hosts`` file:

  .. code-block:: bash

    192.168.33.10 preview.localhost


************************************
Customize the Source Code Location
************************************

You can customize the location of the edX source code that gets cloned when you
provision Devstack. You may want to do this to have Devstack work with source
code that already exists on your computer.

By default, the source code location is the directory in which you run ``vagrant
up``.  To change this location, set the ``VAGRANT_MOUNT_BASE`` environment
variable to set the base directory for the edx-platform and cs_comments_service
source code directories.

.. WHERE IS VARIABLE?

************************************
Run the LMS on Devstack
************************************

When you run the LMS on Devstack, the command updates requirements and
compiles assets, unless you use the ``fast`` option.

The command uses the file ``lms/envs/devstack.py``. This file
overrides production settings for the LMS.

To run the LMS on Devstack:

#. `Connect to the Devstack Virtual Machine`_.
#. Run the following command:
   
   .. code-block:: bash

    paver devstack lms

   Or, to start the LMS without updating requirements and compiling assets, use the ``fast`` option:
   
   .. code-block:: bash

    paver devstack --fast lms 

   The LMS starts. 

#. Open the LMS in your browser at ``http://localhost:8000/``. 

   Vagrant forwards port 8000 to the LMS server running in the virtual machine.


************************************
Run Studio on Devstack
************************************

When you run Studio on Devstack, the command updates requirements and compiles
assets, unless you use the ``fast`` option.

You run Studio on Devstack with the file ``cms/envs/devstack.py``. This file
overrides production settings for Studio.

To run Studio on Devstack:

#. `Connect to the Devstack Virtual Machine`_.
#. Run the following command:
   
   .. code-block:: bash

    paver devstack studio

   Or, to start Studio without updating requirements and compiling assets, use
   the ``fast`` option:
   
   .. code-block:: bash

    paver devstack --fast studio 

   Studio starts. 

#. Open the LMS in your browser at ``http://localhost:8001/``. 
 
   Vagrant forwards port 8001 to the Studio server running in the virtual
   machine.

************************************
Run Discussion Forums on Devstack
************************************

To run discussion forums on Devstack:

#. `Connect to the Devstack Virtual Machine`_.
#. Switch to the discussion forum account:
   
   .. code-block:: bash

    sudo su forum

#. Update Ruby requirements. 

   .. code-block:: bash

    bundle install

   .. note:: 
     If you get a message for entering a password to install the bundled
     RubyGems to the system, you can safely exit by entering ``control+c`` on a
     Macintosh or ``Ctrl+C`` on Windows. The RubyGems will still be installed
     correctly for the forum user.

#. Start the discussion forums server.
   
   .. code-block:: bash

    ruby app.rb -p 18080

The discussions forum server starts. You can access the discussion forums API at
``http://localhost:18080/``.

************************************
Default Accounts on Devstack
************************************

When you install Devstack, the following accounts are created:

  .. list-table::
   :widths: 20 60
   :header-rows: 1

   * - Account
     - Description
   * - staff@example.com
     - An LMS and Studio user with course creation and editing permissions. This
       user is a course staff member with rights to work with the demonstration
       course in Studio.
   * - verified@example.com
     - A student account that you can use to access the LMS for testing verified certificates.
   * - audit@example.com
     - A student account that you can use the access the LMS for testing course auditing.
   * - honor@example.com
     - A student account that you can use the access the LMS for testing honor code certificates.

The password for all of these accounts is ``edx``.
