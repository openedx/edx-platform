class D0CLI(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        
        if not hasattr(self, 'message'):
            self.message = args[0] if args else None

class Unauthorized(D0CLI):
    pass

class Conflict(D0CLI):
    pass

class NotFound(IndexError, D0CLI):
    pass

class UserError(D0CLI):
    pass


class ShowHelp(D0CLI):
    pass

class DOError(Exception):
    pass