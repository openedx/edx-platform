Add a new field to store enable/disabled status of teams
--------------------------------------------------------

Status
======

Proposal


Context
=======

While implementing a UI to enable/disable teams we ran into issues due to the
way teams is considered enabled or disabled, which is with the presence of one
or more teamsets. So enabling requires adding a teamset and disabling requires
removing all teamsets.

Since we'd like to have a simple toggle to enable/disable teams this complicates
the implementation significantly.

Decisions
=========

We can add a new field called ``teams_enabled`` (or simply ``enabled``) to the
``TeamsConfigField`` that stores the teams configuration in the course.

Currently the ``is_enabled`` method on
``openedx.core.lib.teams_config.TeamsConfig`` simply checks that the team_sets
list isn't empty, it should switch to checking for the the ``enabled`` field
instead. It can fall back to the existing behaviour so existing courses work
as-is. However, any update to the value will add this boolean field.

Alternative
===========

Any time teams is disabled, we can move the the existing teams configuration in
the JSON from the key ``team_sets`` to ``teams_sets_inactive``. Existing code will
ignore this field and disable the teams tab and other teams features.

However the new UI can be made aware of this backup field and use it to
reinitialise the teams config based on old data if needed. So if a course is
set up with teams properly with a few teamsets, and the toggle is disabled,
the data will be moved from ``team_sets`` / ``topics`` to ``team_sets_inactive`` and
if teams is enabled again, the data will be moved from ``team_sets_inactive`` to
``team_sets``.

Optionally we can even allow configuring team sets this way before they are
enabled. i.e. in a disabled state all teamset operation can be redirected to
``team_sets_inactive``
