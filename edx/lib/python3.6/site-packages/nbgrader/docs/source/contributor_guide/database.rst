Modifying the Database
======================

Sometimes new features require modifying the database, such as adding a new
column. Implementing such changes is fine, but can cause compatibility problems
for users who are using an older version of the database schema. To resolve
this issue, we use `alembic <http://alembic.zzzcomputing.com/en/latest/index.html>`_ to handle database migrations.

To use alembic to migrate the database schema, first run the following
command::

    python -m nbgrader.dbutil revision -m "a description of the change"

This will create a file in the directory ``nbgrader/alembic/versions``, for
example ``nbgrader/alembic/versions/7685cbef311a_foo.py``. You will now need to
edit the ``upgrade()`` and ``downgrade()`` functions in this file such that
they appropriately make the database changes. For example, to add a column
called ``extra_credit`` to the ``grade`` table:

.. code:: python

    def upgrade():
        op.add_column('grade', sa.Column('extra_credit', sa.Float))

    def downgrade():
        op.drop_column('grade', 'extra_credit')

Please see the `alembic documentation
<http://alembic.zzzcomputing.com/en/latest/index.html>`_ for further details on
how these files work. Additionally, note that you both need to update the
database schema in ``nbgrader/api.py`` (this describes how to create **new**
databases) as well as using alembic to describe what changes need to be made to
**old** databases.

You can test whether the database migration works appropriately by running::

    nbgrader db upgrade

on an old version of the database.
