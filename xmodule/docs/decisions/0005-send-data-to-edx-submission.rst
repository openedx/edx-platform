#########################################################
Implementation to send student response to edx-submission
#########################################################

Status
******

Accepted.

2025-03-13

Context
*******

Traditionally, the Open edX platform has utilized the ``XQueue`` service to handle student assignment submissions. However, to leverage a more modern and efficient architecture, there is a need to transition these submissions to the ``edx-submission`` service. This transition aims to improve the scalability and maintainability of the submission handling process.

Decision
********

The following changes have been implemented to redirect student submissions to the `edx-submission` service:

1. **Introduction of `send_to_submission` Function in `xqueue_submission.py`:**

   - **Functionality:** A new function, `send_to_submission`, has been developed to process student responses. It parses essential information such as `course_id`, `item_id`, `student_id`, and `max_score` from the submission data.

   - **Integration with `edx-submission`:** The function utilizes the API provided by `edx-submission` to create a new submission record in the submissions database, ensuring that student responses are stored and processed accurately with the appropriate `max_score`.

2. **Modification of `xqueue_interfaces.py`:**

   - **Service Selection Logic:** The file `xmodule/capa/xqueue_interfaces.py` has been updated to include a condition that checks the state of the `send_to_submission_course.enable` *waffle flag*. If the flag is active for a specific course, student responses are directed to the `edx-submission` service via the `send_to_submission` function. If inactive, the submissions continue to be processed by `XQueue`.

3. **Temporary Waffle Flag Implementation:**

   - **Definition:** A course-level waffle flag named `send_to_submission_course.enable` has been introduced. Administrators can set this flag via the Django admin interface, enabling or disabling the `edx-submission` functionality for specific courses without requiring code changes.

   - **Deprecation Plan:** This *waffle flag* is a temporary measure to facilitate a smooth transition. Once the `edx-submission` service is fully adopted and validated, the flag will be deprecated, and all submissions will be processed exclusively through `edx-submission`.


Configuration for Xqueue-watcher:
***************************************

Prerequisites
-------------

- Ensure you have the Xqueue repository cloned and running.
- Basic understanding of microservices and Docker (if applicable).

1. Setting up Xqueue-Server
---------------------------

**Requirements:**

First, clone the Xqueue repository into your environment:

.. code-block:: bash

    git clone https://github.com/openedx/xqueue.git

**Steps:**

1. Run the service using either Docker or as a microservice within your environment.
2. Make sure to expose port **18040** since the service listens on this port:

   ::

     http://127.0.0.1:18040

3. Verify that the service is running by accessing the configured URL or checking the service logs.

2. Configuring Xqueue-Watcher
-----------------------------

**Installation:**

1. Clone the Xqueue-Watcher repository:

.. code-block:: bash

    git clone https://github.com/openedx/xqueue-watcher.git

2. Navigate to the project directory and install any necessary dependencies:

.. code-block:: bash

    cd xqueue-watcher
    pip install -r requirements.txt

**Configuration:**

1. Locate the configuration file at:

   ::

     config/conf.d/course.json

2. Update the `course.json` file with the following configuration:

.. code-block:: json

    {
      "test-123": {
        "SERVER": "http://127.0.0.1:18040",
        "CONNECTIONS": 1,
        "AUTH": ["username", "password"]
      }
    }

- **test-123**: The name of the queue to listen to.
- **SERVER**: The Xqueue server address.
- **AUTH**: A list containing `[username, password]` for Xqueue Django user authentication.
- **CONNECTIONS**: Number of threads to spawn to watch the queue.

3. Start the Xqueue-Watcher service:

.. code-block:: bash

    python watcher.py

3. Setting up Xqueue-Submission
-------------------------------

This new flow sends queue data to **edx-submission** for processing.

**Steps:**

1. Create a new instance of Xqueue-Watcher:

.. code-block:: bash

    git clone https://github.com/openedx/xqueue-watcher.git

2. Configure the new instance to listen on port **8000**. Edit the `course.json` file located at:

   ::

     config/conf.d/course.json

3. Add the following configuration:

.. code-block:: json

    {
      "test-123": {
        "SERVER": "http://127.0.0.1:8000",
        "CONNECTIONS": 1,
        "AUTH": ["username", "password"]
      }
    }

- **SERVER**: Now points to port **8000**, where edx-submission is running.

4. Start the new instance of Xqueue-Watcher:

.. code-block:: bash

    python watcher.py

4. Verification
---------------

1. Ensure that all services are running:
   - Verify that ports **18040** and **8000** are active.
   - Check the logs for connection errors or authentication issues.

2. Test the configuration:
   - Send a test request to the queue `test-123` to confirm data processing through **edx-submission**.


Consequences
************

**Positives:**

- **Enhanced Submission Handling:** Transitioning to the `edx-submission` service offers a more modern and efficient architecture for processing student responses, improving scalability and maintainability.

- **Controlled Migration:** The temporary *waffle flag* allows for a phased transition, enabling administrators to test and adopt the new submission process on a per-course basis, thereby minimizing potential disruptions.

**Negatives:**

- **Increased Complexity:** Introducing a temporary flag-based flow adds complexity to the codebase, which may increase maintenance efforts during the transition period.


References
**********

- **Feature Toggles documentation in Open edX**: [Feature Toggles — edx-platform documentation](https://docs.openedx.org/projects/edx-platform/en/latest/references/featuretoggles.html)

- **edx-submissions repository**: [openedx/edx-submissions](https://github.com/openedx/edx-submissions)

- **edx-platform repository**: [openedx/edx-platform](https://github.com/openedx/edx-platform)

- **xqueue repository**: [openedx/xqueue](https://github.com/openedx/xqueue)

- **xqueue-watcher repository**: [openedx/xqueue-watcher](https://github.com/openedx/xqueue-watcher)
