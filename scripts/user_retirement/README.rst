User Retirement Scripts
=======================

This directory contains python scripts which are migrated from the `tubular <https://github.com/openedx/tubular/tree/master/scripts>`_ respository. 
These scripts are intended to drive the user retirement workflow which involves handling the deactivation or removal of user accounts as part of the platform's management process.

Getting Started
===============

Download the Scripts
--------------------

To download the scripts, you can perform a partial clone of the edx-platform repository to obtain only the required scripts. The following steps demonstrate how to achieve this. Alternatively, you may choose other utilities or libraries for the partial clone.

.. code-block:: bash

    repo_url=git@github.com:openedx/edx-platform.git
    branch=master
    directory=scripts/user_retirement

    git clone --branch $branch --single-branch --depth=1 --filter=tree:0 $repo_url
    cd edx-platform
    git sparse-checkout init --cone
    git sparse-checkout set $directory

Create Python Virtual Environment
-----------------------------------

Create a Python virtual environment using Python 3.8:

.. code-block:: bash

    python3.8 -m venv venv
    source venv/bin/activate

Install Pip Packages
---------------------

Install the required pip packages using the provided requirements file:

.. code-block:: bash

    pip install -r scripts/user_retirement/requirements/base.txt

Run Test Cases
--------------

Before running test cases, install the testing requirements:

.. code-block:: bash

    pip install -r scripts/user_retirement/requirements/testing.txt

Run the test cases using pytest:

.. code-block:: bash

    pytest scripts/user_retirement

Comprehensive Documentation and Configuration Steps
===================================================

For in-depth documentation and essential configurations follow these references

`documentation <https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/user_retire/index.html#>`_

`configuration <https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/user_retire/driver_setup.html>`_

Example Script
==============

To retire a specific learner, you can use the provided example script:

.. code-block:: bash

    python scripts/user_retirement/retire_one_learner.py \
    --config_file=src/config.yml \
    --username=user1

Make sure to replace ``src/config.yml`` with the actual path to your configuration file.

Feel free to customize these steps according to your specific environment and requirements.
