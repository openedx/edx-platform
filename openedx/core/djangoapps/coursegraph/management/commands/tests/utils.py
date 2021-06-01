"""
Utilities for testing the dump_to_neo4j management command
"""


from py2neo import Node


class MockGraph(object):
    """
    A stubbed out version of py2neo's Graph object, used for testing.
    Args:
        transaction_errors: a bool for whether transactions should throw
        an error.
    """
    def __init__(self, transaction_errors=False, **kwargs):  # pylint: disable=unused-argument
        self.nodes = set()
        self.number_commits = 0
        self.number_rollbacks = 0
        self.transaction_errors = transaction_errors

    def begin(self):
        """
        A stub of the method that generates transactions
        Returns: a MockTransaction object (instead of a py2neo Transaction)
        """
        return MockTransaction(self)


class MockTransaction(object):
    """
    A stubbed out version of py2neo's Transaction object, used for testing.
    """
    def __init__(self, graph):
        self.temp = set()
        self.graph = graph

    def run(self, query):
        """
        Deletes all nodes associated with a course. Normally `run` executes
        an arbitrary query, but in our code, we only use it to delete nodes
        associated with a course.
        Args:
            query: query string to be executed (in this case, to delete all
            nodes associated with a course)
        """
        start_string = "WHERE n.course_key='"
        start = query.index(start_string) + len(start_string)
        query = query[start:]
        end = query.find("'")
        course_key = query[:end]

        self.graph.nodes = set([
            node for node in self.graph.nodes if node['course_key'] != course_key
        ])

    def create(self, element):
        """
        Adds elements to the transaction's temporary backend storage
        Args:
            element: a py2neo Node object
        """
        if isinstance(element, Node):
            self.temp.add(element)

    def commit(self):
        """
        Takes elements in the transaction's temporary storage and adds them
        to the mock graph's storage. Throws an error if the graph's
        transaction_errors param is set to True.
        """
        if self.graph.transaction_errors:
            raise Exception("fake exception while trying to commit")
        for element in self.temp:
            self.graph.nodes.add(element)
        self.temp.clear()
        self.graph.number_commits += 1

    def rollback(self):
        """
        Clears the transactions temporary storage
        """
        self.temp.clear()
        self.graph.number_rollbacks += 1


class MockNodeSelector(object):
    """
    Mocks out py2neo's NodeSelector class. Used to select a node from a graph.
    py2neo's NodeSelector expects a real graph object to run queries against,
    so, rather than have to mock out MockGraph to accommodate those queries,
    it seemed simpler to mock out NodeSelector as well.
    """
    def __init__(self, graph):
        self.graph = graph

    def select(self, label, course_key):
        """
        Selects nodes that match a label and course_key
        Args:
            label: the string of the label we're selecting nodes by
            course_key: the string of the course key we're selecting node by

        Returns: a MockResult of matching nodes
        """
        nodes = []
        for node in self.graph.nodes:
            if node.has_label(label) and node["course_key"] == course_key:
                nodes.append(node)
        return MockNodeSelection(nodes)


class MockNodeSelection(list):
    """
    Mocks out py2neo's NodeSelection class: this is the type of what
    MockNodeSelector's `select` method returns.
    """
    def first(self):
        """
        Returns: the first element of a list if the list has elements.
            Otherwise, None.
        """
        return self[0] if self else None
