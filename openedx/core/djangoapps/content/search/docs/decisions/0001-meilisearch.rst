Studio Content Search Powered by Meilisearch
############################################

Status
******

Draft


Context
*******

Existing search functionality
=============================

The Open edX platform currently implements many different forms of search. For
example, users can search for course content, library content, forum posts, and
more. Most of the search functionality in the core platform is powered by the
Elasticsearch search engine (though other functionality developed by 2U, such as
in edx-enterprise, is powered by Algolia).

Most uses of Elasticsearch in Open edX use
`edx-search <https://github.com/openedx/edx-search>`_ which provides a partial
abstraction over Elasticsearch. The edx-search library formerly used
`django-haystack <https://django-haystack.readthedocs.io/>`_ as an abstraction
layer across search engines, but "that was ripped out after the package was
abandoned upstream and it became an obstacle to upgrades and efficiently
utilizing Elasticsearch (the abstraction layer imposed significant limits)"
(thanks to Jeremy Bowman for this context). Due to these changes, the current
edx-search API is a mix of abstractions and direct usage of the Elasticsearch
API, which makes it confusing and difficult to work with. In addition, each
usage of edx-search has been implemented fairly differently. See
`State of edx-search <https://openedx.atlassian.net/wiki/spaces/AC/pages/3884744738/State+of+edx-search+2023>`_
for details (thanks to Andy Shultz).

Other platform components use Elasticsearch more directly:

* ``course-discovery`` and ``edx-notes-api`` do not use ``edx-search``, but are
  very tied to Elasticsearch via the use of ``django-elasticsearch-dsl`` and
  ``django-elasticsearch-drf``.
* ``cs_comments_service`` uses Elasticsearch via the official ruby gems.

Problems with Elasticsearch
===========================

At the same time, there are many problems with the current reliance on
Elasticsearch:

1. In 2021, the license of Elasticsearch changed from Apache 2.0 to a more
   restrictive license that prohibits providing "the products to others as a
   managed service". Consequently, AWS forked the search engine to create
   OpenSearch and no longer offers Elasticsearch as a service. This is
   problematic for many Open edX operators that use AWS and prefer to avoid
   any third-party services.
2. Elasticsearch is very resource-intensive and often uses more than a gigabyte
   of memory just for small search use cases.
3. Elasticsearch has poor support for multi-tenancy, which multiplies the
   problem of resource usage for organizations with many small Open edX sites.
4. The existing usage of edx-search/Elasticsearch routes all search requests and
   result processing through edxapp (the LMS) or other IDAs, increasing the
   load on those applications.

Need for Studio Search
======================

At the time of this ADR, we have a goal to implement new search functionality in
Studio, to support various course authoring workflows.

Meilisearch
===========

Meilisearch ("MAY-lee search") is a new, promising search engine that offers a
compelling alternative to Elasticsearch. It is open source, feature rich, and
very fast and memory efficient (written in Rust, uses orders of magnitude less
memory than Elasticsearch for small datasets). It has a simple API with an
official python driver, and has official integrations with the popular
Instantsearch frontend library from Algolia. It has strong support for
multi-tenancy, and allows creating restricted API keys that incorporate a user's
permissions, so that search requests can be made directly from the user to
Meilisearch, rather than routing them through Django. Initial testing has shown
it to be much more developer friendly than Elasticsearch/OpenSearch.

At the time of writing, there are only two known concerns with Meilisearch:

1. It doesn't (yet) support High Availability via replication, although this is
   planned and under development. It does have other features to support high
   availability, such as very low restart time (in ms).
2. It doesn't support boolean operators in keyword search ("red AND panda"),
   though it does of course support boolean operators in filters. This is a
   product decision aimed at keeping the user experience simple, and is unlikely
   to change.


Decision
********

1. We will implement the new Studio search functionality using Meilisearch,
   as an experiment and to evaluate it more thoroughly.
2. The Studio search functionality will be disabled by default in the next
   Open edX release (Redwood), so that Meilisearch will not be a requirement
   for any default nor existing features. This will also allow us to evaluate it
   before deciding to embrace it or replace it.
3. We will keep the Meilisearch-specific code isolated to the
   new ``content/search`` Django app, so it's relatively easy to swap out later
   if this experiment doesn't pan out.
4. We will not use ``edx-search`` for the new search functionality.
5. For the experiment, we won't use Meilisearch during tests, but we expect to
   add that in the future if we move forward with replacing Elasticsearch completely.


Consequences
************

1. Organizations that wish to try out the new Studio Search functionality in
   the Redwood release will have to install and configure Meilisearch.
2. Building both the backend and frontend components of the Studio search
   project will be much faster and simpler than if we used ElasticSearch,
   edx-search, OpenSearch, django-haystack, etc.
3. Keyword search with boolean operators will not be supported in any of the new
   search features.


Alternatives Considered
***********************

OpenSearch Only
===============

Moving existing search functionality to OpenSearch is a possibility, but though
it mostly addresses the licensing issue, it doesn't solve the problems of
resource usage, API complexity, edx-search API complexity, lack of Instantsearch
integration, and poor multi-tenancy.

OpenSearch and Elasticsearch
============================

When OpenSearch was originally forked from Elasticsearch, it was completely API
compatible, but over time they have developed along divergent paths. Regardless
of whether ElasticSearch and OpenSearch are actually wire-compatible, recent
versions of all the official ElasticSearch clients have been made to actively
reject connections to OpenSearch, which is why you generally won't find client
libraries that work with both engines, and why there are OpenSearch forks of
everything on the client side as well as the server side.

As there is no ready-to-use abstraction layer that would allow us to comfortably
support both, and no interest in maintaining one ourselves, this is not an
appealing option.

Algolia
=======

Algolia is a great search engine service, but as it is a proprietary product, it
is not suitable as a requirement for an open source platform like Open edX.
