#########################################################
implementation to send student response to edx-submission
#########################################################

Status
******

Accepted.

2025-02-21

Context
*******

On the Open edX platform, student responses to assignments are traditionally submitted to the `XQueue` service for assessment. However, a need was identified to allow certain responses to be submitted to the `edx-submission` service, which offers a more modern and efficient architecture for handling submissions. To facilitate a controlled transition and allow for A/B testing, the introduction of a *waffle flag* was proposed to enable dynamic selection of the submission service based on the specific course.

Decision
********

A course-level waffle flag called `send_to_submission_course.enable` has been implemented. This flag can be set via the Django admin, allowing administrators to enable or disable the `edx-submission` submission functionality for specific courses without requiring any code changes.

Key changes include:

1. **Waffle Flag Definition**: The `send_to_submission_course.enable` flag was created in the Django admin, associating it with the corresponding `course_id`.

2. **`xqueue_interfaces.py` Modification**: In the `xmodule/capa/xqueue_interfaces.py` file, a condition was added that checks the state of the *waffle flag*. If the flag is on for a given course, student responses are sent to the `edx-submission` service using the `send_to_submission` function. If the flag is off, the flow continues sending responses to `XQueue`.

3. **`construct_callback` Method Update**: Within the `XQueueService` class in `xqueue_interfaces.py`, the `construct_callback` method was modified. This method generates the callback URL that `XQueue` or `edx-submission` will use to return the evaluation results. The method now checks the state of the `send_to_submission_course.enable` *waffle flag* to determine whether the callback URL should point to the `edx-submission` handler (`callback_submission`) or to the original `XQueue` handler (`xqueue_callback`).

4. **Implementation of `send_to_submission` in `xqueue_submission.py`**: The `send_to_submission` function was developed in the `xqueue_submission.py` file. This function is responsible for:
   - **Parse Submission Data**: Extracts and processes relevant information from the student response, including identifiers such as `course_id`, `item_id`, and `student_id`.
   
   - **Interaction with `edx-submission`**: Uses the API provided by `edx-submission` to create a new submission record in the submissions database, ensuring that the student response is stored and processed appropriately.

Configuration for Xqueue-watcher:

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

- **Flexibility**: Administrators can enable or disable the `edx-submission` submission functionality on a per-course basis, facilitating controlled testing and a smooth transition.

- **Improved Submission Handling**: By using `edx-submission`, you can take advantage of a more modern architecture for processing responses.

**Negatives:**

- **Additional Complexity**: The introduction of a new flag-based flow adds complexity to the code, which can increase maintenance effort.

- **Potential Inconsistency**: If flag states are not properly managed, there could be inconsistencies in submission handling across courses.

References
**********

- **Relevant commits**: [Implementation of the Waffle Flag and modification of xqueue_interfaces.py](https://github.com/aulasneo/edx-platform/commit/f50afcc301bdc3eeb42a 6dc2c051ffb2d799f868#diff-9b4290d2b574f54e4eca7831368727f7ddbac8292aa75ba4b28651d4bf2bbe6b)

- **Feature Toggles documentation in Open edX**: [Feature Toggles — edx-platform documentation](https://docs.openedx.org/projects/edx-platform/en/latest/references/featuretoggles.html)

- **edx-submissions repository**: [openedx/edx-submissions](https://github.com/openedx/edx-submissions)

- **edx-platform repository**: [openedx/edx-platform](https://github.com/openedx/edx-platform)

- **xqueue repository**: [openedx/xqueue](https://github.com/openedx/xqueue)

- **xqueue-watcher repository**: [openedx/xqueue-watcher](https://github.com/openedx/xqueue-watcher)
