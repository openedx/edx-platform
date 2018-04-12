Journals
---------

This directory contains a Django application that allows a learners to interact
with a content Journal. The majority of the capabilities
are provided through the Journals IDA here: `https://github.com/edx/journals`
and through Journal modules added to Discovery and Ecommerce services.

**Journal**:

The Journal is a new product type that will be offered for purchase in the LMS. It is indepedent from a course, and contains a collection of resources/content-types (documents, videos, rich text, etc) that can be updated easily through the Journal service. A Journal is linked to an organization and you can purchase/receive access to it. One notable difference is that a Journal will have an access_length, which determines the amount of time the learner will have access to it post-purchase. This is our first stage towards a subscription model. The Discovery Service is the source-of-truth for all Journal related marketing information that is displayed in the LMS.

**JournalBundle**:

The Journal Bundle is a collection of Journals and Courses. It works similar to a program in the bundling aspect, the difference lies in the fact that it doesn't necessarily constitute a progression of courses. The first (and possibly most common) use case that will use this is bundling a single course with a single journal. Journal Bundles are defined in Discovery Service.

**Things to note**:

- The Journals app was intentionally decoupled as much as possible from the rest of the LMS, both for future developer sanity, and to minimally affect the rest of the platform should the scope of the Journals product change.

- The Journals product has a seperate IDA (Journals) which works as the publishing platform, the consumption platform, and the marketing platform (for standalone Journals). This is different from the structure of studio/lms and so some information may be handled differently in this application.

**Functionality Added to LMS to support Journals**:

- "Cards" for Journals and Journal Bundles on main LMS index page such that learners can discover and purchase Journals. These are the equivalent to course cards and Program cards in the LMS. 

- Journals dashboard, that lists Journals that have been purchased by the learner. Similar to Programs dashboard in LMS.

**API**:

api.py - This class provides an abstraction to Journal specific information that is needed by the LMS. Specifically, it provides an api to fetch Journals and Journal Bundles from the Discovery Service, both of which are needed to display Journals information on main LMS index page as well as dashboard. Additionally it provides an api to fetch JournalAccess records from the Journal Service. This is used to determine which Journals a user has access to and displays this information on the "Journals" Dashboard.

**Views**:

learner_dashboard.py: This view adds a "Journals" tab to the dashboard and displays a list of Journals that the learner has access to. Clicking on a Journal from the dashboard will direct learner to the Journal Service to view the Journal.

marketing.py: This view provides a marketing page for Journal Bundles. It can be thought of as the equivalent to a Program About page. Specifically, it will show information about Journal(s) and Course(s) which have been bundled together for marketing and discouting purposes. The bundle definition and meta-data lives in the Discovery service.
