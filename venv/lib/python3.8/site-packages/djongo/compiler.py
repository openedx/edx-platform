class SQLCompiler:

    def __init__(self, query, connection, using):
        self.query = query
        self.connection = connection
        self.using = using
