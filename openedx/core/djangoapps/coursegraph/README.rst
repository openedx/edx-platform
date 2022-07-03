
Coursegraph Support
-------------------

This app exists to write data to "Coursegraph", a tool enabling Open edX developers and support specialists to inspect their platform instance's learning content. Coursegraph itself is simply an instance of Neo4j, which is an open-source graph database with a web interface.

Deploying Coursegraph
=====================

As of the Maple Open edX release, Coursegraph is *not* automatically provisioned by the community installation, and is *not* considered a "supported" part of the platform. However, operators may find the `neo4j Ansible playbook`_ useful as a starting point for deploying their own Coursegraph instance. Alternatively, Neo4j also maintains an official `Docker image`_.

In order for Coursegraph to have queryable data, learning content from LMS must be written to Coursegraph using the ``dump_to_neo4j`` management command included in this app. In order for the data to stay up to date, it must be periodically refreshed, either manually or via an automation server such as Jenkins.

**Please note**: Access to a populated Coursegraph instance confers access to all the learning content in the related Open edX LMS/CMS. The basic authentication provided by Neo4j may or may not be sufficient for your security needs. Consider taking additional security measures, such as restricting Coursegraph access to only users on a private VPN.

.. _neo4j Ansible playbook: https://github.com/edx/configuration/blob/master/playbooks/neo4j.yml

.. _Docker image: https://neo4j.com/developer/docker-run-neo4j/


Coursegraph in Devstack
=======================

Coursegraph is included as an "extra" component in the `Open edX Devstack`_. That is, it is not run or provisioned by default, but can be enabled on-demand.

To provision Devstack Coursegraph with data from Devstack LMS, run::

  make dev.provision.coursegraph

Coursegraph should now be accessible at http://localhost:7474 with the username ``neo4j`` and the password ``edx``.

Under the hood, the provisioning command just invokes ``dump_to_neo4j`` on your LMS, pointed at your Coursegraph. The provisioning command can be run again at any point in the future to refresh Coursegraph with new LMS data. The data in Coursegraph will persist unless you explicitly destroy it (as noted below).

Other Devstack Coursegraph commands include::

  make dev.up.coursegraph       # Bring up the container (without re-provisioning).
  make dev.down.coursegraph     # Stop and remove the container.
  make dev.shell.coursegraph    # Start a shell session in the container.
  make dev.attach.coursegraph   # Attach to the container.
  make dev.destroy.coursegraph  # Stop the container and destroy its database.

The above commands should be run in your ``devstack`` folder, and they assume that LMS is already properly provisioned. See the `Devstack interface`_ for more details.

.. _Open edX Devstack: https://github.com/edx/devstack/
.. _Devstack interface: https://edx.readthedocs.io/projects/open-edx-devstack/en/latest/devstack_interface.html


Querying Coursegraph
====================

Coursegraph is queryable using the `Cypher`_ query language. Open edX learning content is represented in Neo4j using a straightforward scheme:

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
