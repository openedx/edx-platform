Transition away from legacy discussions experience
==================================================


Status
------

Proposal


Context
-------

To date, all courses in the LMS are automatically provided with
Discussions via the legacy EdX system (`cs_comments_service`).
The Discussions Tab cannot be hidden via Studio (though possibly via
manual XML edits during Course Import?).


Requirements
------------

- The existing discussions experience should be configurable via the new
  Course Authoring MFE _before_ we switch to the new Discussions MFE
  experience.
- Existing courses should not be prompted to select a discussion
  provider; they get the legacy experience, unless manually overridden
  via Djano Admin.
- Only new courses, after broad rollout, should be prompted to select an
  available provider.


Decision
--------

We propose to handle the transition as follows:

Data
~~~~
- Backfill `DiscussionsConfiguration` table for existing courses
  - If no config exists yet, create entry with `provider=legacy`
  - TODO: What about `external_forum_url` setting?
- Until we start allowing (requiring?) instructors to choose provider
  - Add to `DiscussionsConfiguration` table for new courses
- Once we require choice
  - _Stop_ auto-provisioning `DiscussionsConfiguration` for new courses


Display
~~~~~~~
- When entry does _not_ exist in `DiscussionsConfiguration`
  - Discussions tile on P&R links to provider selection screen
  - Discussion tab will _not_ be present in the LMS (post-backfill).
- When entry exists in `DiscussionsConfiguration`
  - Discussions tile on P&R links to provider configuration screen
  - Discussion tab _will_ be present in the LMS (if enabled).
