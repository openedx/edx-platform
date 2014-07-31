"""
Implement interfaces for representing runtime objects in XBlock.

Do not persist along with the xblock. Just a representation of runtime object.
"""

class XBlockModel(object):
    """
    Interface to represent an xblock model.

    By providing an interface, workbench can dynamically define the 
    attributes for each XBlockModel object that is bound to an xblock

    This Model allows a very flexible transfer of workbench objects 
    to the given XBlock instance.
    """

    def __init__(self, parent, **kwargs):
        """
        Constructor for XBlockUser takes in kwargs of attr and vals to rep
        the object. The parent in the xblock to which this model will be 
        bound.
        """
        self.parent = parent

        for attr, val in kwargs.iteritems():
            self.add_attribute(attr, val)

    def add_attr(self, attr, value):
        """
        Sets a new attribute attr_name of value to the XBlock Model instance 
        """
        setattr(self, attr, value)
    

class XBlockUser(XBlockModel):
    """
    XBlock's user model representation during runtime. 

    XBlock provides a set of predefined attributes as instance variables.
        - email
        - full_name
        - user_name
        - anon_id
        - is_instructor

    Runtimes are not required to conform to this standard and can always
    use kwargs and att_attr to patch attributes dynamically
    """
    def __init__(self, parent, email="", full_name="", user_name="", anon_id="", is_instructor=False, **kwargs):

        # Set standardized attributes
        self.email = email
        self.full_name = full_name
        self.user_name = user_name
        self.anon_id = anon_id
        self.is_instructor = is_instructor
        
        # Set all dynamic attributes
        super(XBlockUser, self).__init__(parent, **kwargs)