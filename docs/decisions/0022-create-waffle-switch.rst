###############################################################
Integration of Waffle Switch for XQueue Submission
###############################################################

Status
******

**Pending** *2025-02-11*

Implementation in progress.

Context
*******

In the `edx-platform` repository, there was a need to implement a mechanism that allows conditional execution of a new functionality: sending a student's response within an exercise to the `created_submission` function. This mechanism should be easily toggleable without requiring code changes or deployments.

Decision
********

A `waffle switch` named `xqueue_submission.enabled` was introduced within the Django admin interface. When this switch is activated, it enables the functionality to send data to the `send_to_submission` function, which parses and forwards the data to the `created_submission` function.

The `created_submission` function resides in the `edx-submissions` repository and is responsible for storing the data in the submissions database.

Implementation Details
----------------------

This functionality was implemented within the `edx-platform` repository by modifying the following files:

1. **`xmodule/capa/xqueue_interfaces.py`**  
   - The `waffle switch` **`xqueue_submission.enabled`** was added here.
   - This switch is checked before invoking `send_to_submission`, ensuring that the submission logic is only executed when enabled.

2. **`xmodule/capa/xqueue_submission.py`**  
   - This file contains the newly implemented logic that parses the student’s response.
   - It processes and formats the data before calling `created_submission`, ensuring that it is correctly stored in the **edx-submissions** repository.

Consequences
************

Positive:
---------

- **Flexibility:** The use of a `waffle switch` allows administrators to enable or disable the new submission functionality without modifying the codebase or redeploying the application.
- **Control:** Administrators can manage the feature directly from the Django admin interface, providing a straightforward method to toggle the feature as needed.
- **Modular Design:** The logic was added in a way that allows future modifications without affecting existing submission workflows.

Negative:
---------

- **Potential Misconfiguration:** If the `waffle switch` is not properly managed, there could be inconsistencies in submission processing.
- **Admin Overhead:** Requires monitoring to ensure the toggle is enabled when needed.

References
**********

- Commit implementing the change: [f50afcc301bdc3eeb42a6dc2c051ffb2d799f868#diff-9b4290d2b574f54e4eca7831368727f7ddbac8292aa75ba4b28651d4bf2bbe6b](https://github.com/aulasneo/edx-platform/commit/f50afcc301bdc3eeb42a6dc2c051ffb2d799f868#diff-9b4290d2b574f54e4eca7831368727f7ddbac8292aa75ba4b28651d4bf2bbe6b)
- Open edX Feature Toggles Documentation: [Feature Toggles — edx-platform documentation](https://docs.openedx.org/projects/edx-platform/en/latest/references/featuretoggles.html)
- `edx-submissions` Repository: [openedx/edx-submissions](https://github.com/openedx/edx-submissions)