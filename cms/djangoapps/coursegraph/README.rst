
CourseGraph Support
-------------------

This app exists to write data to "CourseGraph", a tool enabling Open edX developers and support specialists to inspect their platform instance's learning content. CourseGraph itself is simply an instance of `Neo4j`_, which is an open-source graph database with a Web interface.

.. _Neo4j: https://neo4j.com

Deploying Coursegraph
=====================

There are two ways to deploy CourseGraph:

* For operators using Tutor, there is a `CourseGraph plugin for Tutor`_ that is currently released as "Beta". Nutmeg is the earliest Open edX release that the plugin will work alongside.

* For operators still using the old Ansible installation pathway, there exists a `neo4j Ansible playbook`_. Be warned that this method is not well-documented nor officially supported.

In order for CourseGraph to have queryable, up-to-date data, learning content from CMS must be written to CourseGraph regularly. That is where this Django app comes into play. For details on the various ways to write CMS data to CourseGraph, visit the `operations section of the CourseGraph Tutor plugin docs`_.

**Please note**: Access to a populated CourseGraph instance confers access to all the learning content in the associated Open edX CMS (Studio). The basic authentication provided by Neo4j may or may not be sufficient for your security needs. Consider taking additional security measures, such as restricting CourseGraph access to only users on a private VPN.

.. _neo4j Ansible playbook: https://github.com/openedx/configuration/blob/master/playbooks/neo4j.yml

.. _CourseGraph plugin for Tutor: https://github.com/openedx/tutor-contrib-coursegraph/

.. _operations section of the CourseGraph Tutor plugin docs: https://github.com/openedx/tutor-contrib-coursegraph/#managing-data

Running CourseGraph locally
===========================

In some circumstances, you may want to run CourseGraph locally, connected to a development-mode Open edX instance. You can do this in both Tutor and Devstack.

Tutor
*****

The `CourseGraph plugin for Tutor`_ makes it easy to install, configure, and run CourseGraph for local development.

Devstack
********

CourseGraph is included as an "extra" component in the `Open edX Devstack`_. That is, it is not run or provisioned by default, but can be enabled on-demand.

To provision Devstack CourseGraph with data from Devstack LMS, run::

  make dev.provision.coursegraph

CourseGraph should now be accessible at http://localhost:7474 with the username ``neo4j`` and the password ``edx``.

Under the hood, the provisioning command just invokes ``dump_to_neo4j`` on your LMS, pointed at your CourseGraph. The provisioning command can be run again at any point in the future to refresh CourseGraph with new LMS data. The data in CourseGraph will persist unless you explicitly destroy it (as noted below).

Other Devstack CourseGraph commands include::

  make dev.up.coursegraph       # Bring up the container (without re-provisioning).
  make dev.down.coursegraph     # Stop and remove the container.
  make dev.shell.coursegraph    # Start a shell session in the container.
  make dev.attach.coursegraph   # Attach to the container.
  make dev.destroy.coursegraph  # Stop the container and destroy its database.

The above commands should be run in your ``devstack`` folder, and they assume that LMS is already properly provisioned. See the `Devstack interface`_ for more details.

.. _Open edX Devstack: https://github.com/openedx/devstack/
.. _Devstack interface: https://edx.readthedocs.io/projects/open-edx-devstack/en/latest/devstack_interface.html


Querying Coursegraph
====================

CourseGraph is queryable using the `Cypher`_ query language. Open edX learning content is represented in Neo4j using a straightforward scheme:

* A node is an XBlock usage.

* Nodes are tagged with their ``block_type``, such as:

  * ``course``
  * ``chapter``
  * ``sequential``
  * ``vertical``
  * ``problem``
  * ``html``
  * etc.

* Every node is also tagged with ``item``.

* Parent-child relationships in the course hierarchy are reflected in the ``PARENT_OF`` relationship.

* Ordered sibling relationships in the course hierarchy are reflected in the ``PRECEDES`` relationship.

* Fields on each XBlock usage (``.display_name``, ``.data``, etc) are available on the corresponding node.

.. _Cypher: https://neo4j.com/developer/cypher/


Example Queries
***************

How many XBlocks exist in the LMS, by type? ::

  MATCH
      (c:course) -[:PARENT_OF*]-> (n:item)
  RETURN
      distinct(n.block_type) as block_type,
      count(n) as number
  order by
      number DESC


In a given course, which units contain problems with custom Python grading code? ::

  MATCH
      (c:course) -[:PARENT_OF*]-> (u:vertical) -[:PARENT_OF*]-> (p:problem)
  WHERE
      p.data CONTAINS 'loncapa/python'
  AND
      c.course_key = '<course_key>'
  RETURN
      u.location

You can see many more examples of useful CourseGraph queries on the `query archive wiki page`_.

.. _query archive wiki page: https://openedx.atlassian.net/wiki/spaces/COMM/pages/3273228388/Useful+CourseGraph+Queries
