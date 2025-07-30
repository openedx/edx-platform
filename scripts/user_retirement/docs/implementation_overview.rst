.. _Implmentation:

#######################
Implementation Overview
#######################

In the Open edX platform, the user experience is enabled by several
services, such as LMS, Studio, ecommerce, credentials, discovery, and more.
Personally Identifiable Identification (PII) about a user can exist in many of
these services. As a consequence, to remove a user's PII, you must be able
to request each service containing PII to remove, delete, or unlink the
data for that user in that service.

In the user retirement feature, a centralized process (the *driver* scripts) 
orchestrates all of these requests. For information about how to configure the 
driver scripts, see :ref:`driver-setup`.

****************************
The User Retirement Workflow
****************************

The user retirement workflow is a configurable pipeline of building-block
APIs. These APIs are used to:

  * "Forget" a retired user's PII
  * Prevent a retired user from logging back in
  * Prevent re-use of the username or email address of a retired user

Depending on which third parties a given Open edX instance integrates with,
the user retirement process may need to call out to external services or to
generate reports for later processing. Any such reports must subsequently be
destroyed.

Configurability and adaptability were design goals from the beginning, so this
user retirement tooling should be able to accommodate a wide range of Open edX
sites and custom use cases.

The workflow is designed to be linear and rerunnable, allowing recovery and
continuation in cases where a particular stage fails.  Each user who has
requested retirement will be individually processed through this workflow, so
multiple users could be in the same state simultaneously.  The LMS is the
authoritative source of information about the state of each user in the
retirement process, and the arbiter of state progressions, using the
``UserRetirementStatus`` model and associated APIs.  The LMS also holds a
table of the states themselves (the ``RetirementState`` model), rather than
hard-coding the states.  This was done because we cannot predict all the
possible states required by all members of the Open edX community.

This example state diagram outlines the pathways users follow throughout the
workflow:

.. graphviz::
    digraph retirement_states_example {
        ranksep = "0.3";

        node[fontname=Courier,fontsize=12,shape=box,group=main]
        { rank = same INIT[style=invis] PENDING }
        INIT -> PENDING;
        "..."[shape=none]
        PENDING -> RETIRING_ENROLLMENTS -> ENROLLMENTS_COMPLETE -> RETIRING_FORUMS -> FORUMS_COMPLETE -> "..." -> COMPLETE;

        node[group=""];
        RETIRING_ENROLLMENTS -> ERRORED;
        RETIRING_FORUMS -> ERRORED;
        PENDING -> ABORTED;

        subgraph cluster_terminal_states {
            label = "Terminal States";
            labelloc = b  // put label at bottom
            {rank = same ERRORED COMPLETE ABORTED}
        }
    }

Unless an error occurs internal to the user retirement tooling, a user's
retirement state should always land in one of the terminal states.  At that
point, either their entry should be cleaned up from the
``UserRetirementStatus`` table or, if the state is ``ERRORED``, the
administrator needs to examine the error and resolve it. For more information,
see :ref:`recovering-from-errored`.

*******************
The User Experience
*******************

From the learner's perspective, the vast majority of this process is obscured.
The Account page contains a new section titled **Delete My Account**. In this
section, a learner may click the **Delete My Account** button and enter
their password to confirm their request.  Subsequently, all of the learner's
browser sessions are logged off, and they become locked out of their account.

An informational email is immediately sent to the learner to confirm the
deletion of their account. After this email is sent, the learner has a limited
amount of time (defined by the ``--cool_off_days`` argument described in
:ref:`driver-setup`) to contact the site administrators and rescind their
request.

At this point, the learner's account has been deactivated, but *not* retired.
An entry in the ``UserRetirementStatus`` table is added, and their state set to
``PENDING``.

By default, the **Delete My Account** section is visible and the button is
enabled, allowing account deletions to queue up.  The
``ENABLE_ACCOUNT_DELETION`` feature in django settings toggles the visibility
of this section.  See :ref:`django-settings`.

================
Third Party Auth
================

Learners who registered using social authentication must first unlink their
LMS account from their third-party account. For those learners, the **Delete
My Account** button will be disabled until they do so; meanwhile, they will be
instructed to follow the procedure in this help center article: `How do I link
or unlink my edX account to a social media
account?  <https://support.edx.org/hc/en-us/articles/207206067>`_.

.. include:: ../../../../links/links.rst
