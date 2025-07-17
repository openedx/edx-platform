Frontend code and ESLint removal
################################

Status
******

Accepted

Context
*******

Over many years work has been underway to extract frontend code from
edx-platform, to be replaced by MFEs.

Additionally, as of March 2025, edx-platform had more than 700 violations in
ESLint.

For more details on the MFE replacement, see:

- Top-level issue for edx-platform: https://github.com/openedx/edx-platform/issues/31620
- The parent issue of the above issue, which includes IDA frontends: https://github.com/openedx/wg-frontend/issues/156
- Details of the replacement MFEs are noted in the `MFE Rewrite Tracker`_.

.. _MFE Rewrite Tracker: https://openedx.atlassian.net/wiki/spaces/COMM/pages/4262363137/MFE+Rewrite+Tracker

Decision
********

Over these years of work, it was decided that all frontend code should
ultimately be removed from edx-platform. Until this time, there has not yet
been a single ADR or DEPR to capture this decision.

This decision record is to document this past decision. It is ok to add
additional links or details over time to clarify how this extraction will be
accomplished, or to one day celebrate its completion.

Additionally, it has been decided to preemptively remove ESLint. This will
ensure that engineers can stay focused on higher priority work, rather than
spending time fixing linting issues in JavaScript that will simply be removed.
This removal is important because github has started posting these violations
in github comments that make this work seem like a priority. At the very least,
these are annoying messages that clutter up PRs.

Consequences
************

We will continue to replace all frontend code in edx-platform with an
appropriate set of MFEs.
