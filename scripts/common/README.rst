Common Scripts
==============

`This <https://github.com/openedx/edx-platform/tree/master/scripts/common>`_ directory contains some common python scripts. Some of them are migrated from the other repositories.

These scripts could be called from any automation/CD framework.

How to run the scripts
======================

Download the Scripts
--------------------

To download the scripts, you can perform a partial clone of the edx-platform repository to obtain only the required scripts. The following steps demonstrate how to achieve this. Alternatively, you may choose other utilities or libraries for the partial clone.

.. code-block:: bash

    repo_url=git@github.com:openedx/edx-platform.git
    branch=master
    directory=scripts/common

    git clone --branch $branch --single-branch --depth=1 --filter=tree:0 $repo_url
    cd edx-platform
    git sparse-checkout init --cone
    git sparse-checkout set $directory

Create Python Virtual Environment
---------------------------------

Create a Python virtual environment using Python 3.8:

.. code-block:: bash

    python3.8 -m venv ../venv
    source ../venv/bin/activate

Install Pip Packages
--------------------

Install the required pip packages using the provided requirements file:

.. code-block:: bash

    pip install -r scripts/common/requirements/base.txt


Execute Script
--------------

You can simply execute Python scripts with python command

.. code-block:: bash

    python scripts/common/structures.py prune plan_file.json

Feel free to customize these steps according to your specific environment and requirements.

Run Test Cases
==============

Before running test cases, install the testing requirements:

.. code-block:: bash

    pip install -r scripts/common/requirements/testing.txt

Run the test cases using pytest:

.. code-block:: bash

    pytest scripts/common
