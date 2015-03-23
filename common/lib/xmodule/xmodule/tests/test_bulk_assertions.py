import ddt
import itertools
from xmodule.tests import BulkAssertionTest


STATIC_PASSING_ASSERTIONS = (
    ('assertTrue', True),
    ('assertFalse', False),
    ('assertIs', 1, 1),
    ('assertEqual', 1, 1),
    ('assertEquals', 1, 1),
    ('assertIsNot', 1, 2),
    ('assertIsNone', None),
    ('assertIsNotNone', 1),
    ('assertIn', 1, (1, 2, 3)),
    ('assertNotIn', 5, (1, 2, 3)),
    ('assertIsInstance', 1, int),
    ('assertNotIsInstance', '1', int),
    ('assertItemsEqual', [1, 2, 3], [3, 2, 1])
)

STATIC_FAILING_ASSERTIONS = (
    ('assertTrue', False),
    ('assertFalse', True),
    ('assertIs', 1, 2),
    ('assertEqual', 1, 2),
    ('assertEquals', 1, 2),
    ('assertIsNot', 1, 1),
    ('assertIsNone', 1),
    ('assertIsNotNone', None),
    ('assertIn', 5, (1, 2, 3)),
    ('assertNotIn', 1, (1, 2, 3)),
    ('assertIsInstance', '1', int),
    ('assertNotIsInstance', 1, int),
    ('assertItemsEqual', [1, 1, 1], [1, 1])
)

CONTEXT_PASSING_ASSERTIONS = (
    ('assertRaises', KeyError, {}.__getitem__, '1'),
    ('assertRaisesRegexp', KeyError, "1", {}.__getitem__, '1'),
)

CONTEXT_FAILING_ASSERTIONS = (
    ('assertRaises', ValueError, lambda: None),
    ('assertRaisesRegexp', KeyError, "2", {}.__getitem__, '1'),
)


@ddt.ddt
class TestBulkAssertionTestCase(BulkAssertionTest):

    def _run_assertion(self, assertion_tuple):
        assertion, args = assertion_tuple[0], assertion_tuple[1:]
        getattr(self, assertion)(*args)

    @ddt.data(*(STATIC_PASSING_ASSERTIONS + CONTEXT_PASSING_ASSERTIONS))
    def test_passing_asserts_passthrough(self, assertion_tuple):
        self._run_assertion(assertion_tuple)

    @ddt.data(*(STATIC_FAILING_ASSERTIONS + CONTEXT_FAILING_ASSERTIONS))
    def test_failing_asserts_passthrough(self, assertion_tuple):
        # Use super(BulkAssertionTest) to make sure we get un-adulturated assertions
        with super(BulkAssertionTest, self).assertRaises(AssertionError):
            self._run_assertion(assertion_tuple)

    @ddt.data(*CONTEXT_PASSING_ASSERTIONS)
    @ddt.unpack
    def test_passing_context_assertion_passthrough(self, assertion, *args):
        assertion_args = []
        args = list(args)

        exception = args.pop(0)

        while not callable(args[0]):
            assertion_args.append(args.pop(0))

        function = args.pop(0)
        print assertion_args, function, args

        with getattr(self, assertion)(exception, *assertion_args):
            function(*args)

    @ddt.data(*CONTEXT_FAILING_ASSERTIONS)
    @ddt.unpack
    def test_failing_context_assertion_passthrough(self, assertion, *args):
        assertion_args = []
        args = list(args)

        exception = args.pop(0)

        while not callable(args[0]):
            assertion_args.append(args.pop(0))

        function = args.pop(0)

        with super(BulkAssertionTest, self).assertRaises(AssertionError):
            with getattr(self, assertion)(exception, *assertion_args):
                function(*args)

    @ddt.data(*list(itertools.product(
        CONTEXT_PASSING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS
    )))
    @ddt.unpack
    def test_bulk_assert(self, passing_assertion, failing_assertion1, failing_assertion2):
        contextmanager = self.bulk_assertions()

        contextmanager.__enter__()
        super(BulkAssertionTest, self).assertIsNotNone(self._manager)
        self._run_assertion(passing_assertion)
        self._run_assertion(failing_assertion1)
        self._run_assertion(failing_assertion2)

        # Use super(BulkAssertionTest) to make sure we get un-adulturated assertions
        with super(BulkAssertionTest, self).assertRaises(AssertionError):
            contextmanager.__exit__(None, None, None)

    @ddt.data(*list(itertools.product(
        CONTEXT_PASSING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS
    )))
    @ddt.unpack
    def test_bulk_assert_closed(self, passing_assertion, failing_assertion1, failing_assertion2):
        with super(BulkAssertionTest, self).assertRaises(AssertionError):
            with self.bulk_assertions():
                self._run_assertion(passing_assertion)
                self._run_assertion(failing_assertion1)

        # Use super(BulkAssertionTest) to make sure we get un-adulturated assertions
        with super(BulkAssertionTest, self).assertRaises(AssertionError):
            self._run_assertion(failing_assertion2)
