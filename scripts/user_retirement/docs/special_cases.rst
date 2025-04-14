.. _handling-special-cases:

######################
Handling Special Cases
######################

.. _recovering-from-errored:

Recovering from ERRORED
***********************

If a retirement API indicates failure (4xx or 5xx status code), the driver
immediately sets the user's state to ``ERRORED``.  To debug this error state,
check the ``responses`` field in the user's row in
``user_api_userretirementstatus`` (User Retirement Status) for any relevant
logging. Once the issue is resolved, you need to manually set the user's
``current_state`` to the state immediately prior to the state which should be
re-tried.  You can do this using the Django admin. In this example, a user
retirement errored during forums retirement, so we manually reset their state
from ``ERRORED`` to ``ENROLLMENTS_COMPLETE``.

.. graphviz::
   :align: center

    digraph G {
      //rankdir=LR;  // Rank Direction Left to Right
      ranksep = "0.3";

      edge[color=grey]

      node[fontname=Courier,fontsize=12,shape=box,group=main]
      { rank = same INIT[style=invis] PENDING }
      {
          edge[style=bold,color=black]
          INIT -> PENDING;
          "..."[shape=none]
          PENDING -> RETIRING_ENROLLMENTS -> ENROLLMENTS_COMPLETE -> RETIRING_FORUMS;
      }
      RETIRING_FORUMS -> FORUMS_COMPLETE -> "..." -> COMPLETE

      node[group=""];
      RETIRING_ENROLLMENTS -> ERRORED;
      RETIRING_FORUMS -> ERRORED[style=bold,color=black];
      PENDING -> ABORTED;

      subgraph cluster_terminal_states {
          label = "Terminal States";
          labelloc = b  // put label at bottom
          {rank = same ERRORED COMPLETE ABORTED}
      }

      ERRORED -> ENROLLMENTS_COMPLETE[style="bold,dashed",color=black,label=" via django\nadmin"]
    }

Now, the user retirement driver scripts will automatically resume this user's
retirement the next time they are executed.

Rerunning some or all states
*****************************

If you decide you want to rerun all retirements from the beginning, set
``current_state`` to ``PENDING`` for all retirements with ``current_state`` ==
``COMPLETE``.  This would be useful in the case where a new stage in the user
retirement workflow is added after running all retirements (but before the
retirement queue is cleaned up), and you want to run all the retirements
through the new stage.  Or, perhaps you were developing a stage/API that
didn't work correctly but still indicated success, so the pipeline progressed
all users into ``COMPLETED``.  Retirement APIs are designed to be idempotent,
so this should be a no-op for stages already run for a given user.

Cancelling a retirement
***********************

Users who have recently requested account deletion but are still in the
``PENDING`` retirement state may request to rescind their account deletion by
emailing or otherwise contacting the administrators directly.  edx-platform
offers a Django management command that administrators can invoke manually to
cancel a retirement, given the user's email address.  It restores a given
user's login capabilities and removes them from all retirement queues.  The
syntax is as follows:

.. code-block:: bash

   $ ./manage.py lms --settings=<your-settings> cancel_user_retirement_request <email-of-user-to-cancel-retirement>

Keep in mind, this will only work for users which have not had their retirement
states advance beyond ``PENDING``. Additionally, the user will need to reset
their password in order to restore access to their account.
