class InstanceStore(object):
    """
    Interface for accessing instances
    """

    def __init__(self, instance_db, definition_store, policy_store):
        """
        Needs to know where to find the instance stubs, and how to look up
        definitions and policies
        """

        # Lazy version:

        #  - if thing instance_db actually stores parent pointers
        #  directly, doesn't have to do anything.  Mongo should.

        #  - if not, need to load at least a course at a time to get inheritance right.

        pass

    def get(course_id, instance_id):
        """
        Return the specified instance.  Makes sure policy inheritance is done right.
        """


