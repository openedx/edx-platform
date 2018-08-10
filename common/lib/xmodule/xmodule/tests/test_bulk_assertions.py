import ddt
import itertools
from xmodule.tests import BulkAssertionTest, BulkAssertionError

ASSERTION_METHODS_DICT = {
    "GETITEM_SPECIAL_METHOD": {}.__getitem__,
    "LAMBDA": lambda: None
}

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
    ('assertRaises', KeyError, "GETITEM_SPECIAL_METHOD", '1'),
    ('assertRaisesRegexp', KeyError, "1", "GETITEM_SPECIAL_METHOD", '1'),
)

CONTEXT_FAILING_ASSERTIONS = (
    ('assertRaises', ValueError, "LAMBDA"),
    ('assertRaisesRegexp', KeyError, "2", "GETITEM_SPECIAL_METHOD", '1'),
)


@ddt.ddt
class TestBulkAssertionTestCase(BulkAssertionTest):
    shard = 1

    # We have to use assertion methods from the base UnitTest class,
    # so we make a number of super calls that skip BulkAssertionTest.

    # pylint: disable=bad-super-call

    def _is_arg_in_assertion_methods_dict(self, argument):
        """
        Takes in an argument, and returns whether
        """
        return type(argument) == str and argument in ASSERTION_METHODS_DICT

    def _run_assertion(self, assertion_tuple):
        """
        Run the supplied tuple of (assertion, *args) as a method on this class.
        """
        assertion, args = assertion_tuple[0], assertion_tuple[1:]
        args_list = list(args)
        for index, argument in enumerate(args_list):
            if self._is_arg_in_assertion_methods_dict(argument):
                args_list[index] = ASSERTION_METHODS_DICT[argument]
        args = tuple(args_list)
        getattr(self, assertion)(*args)

    def _raw_assert(self, assertion_name, *args, **kwargs):
        """
        Run an un-modified assertion.
        """
        # Use super(BulkAssertionTest) to make sure we get un-adulturated assertions
        return getattr(super(BulkAssertionTest, self), 'assert' + assertion_name)(*args, **kwargs)

    @ddt.data(*(STATIC_PASSING_ASSERTIONS + CONTEXT_PASSING_ASSERTIONS))
    def test_passing_asserts_passthrough(self, assertion_tuple):
        self._run_assertion(assertion_tuple)

    @ddt.data(*(STATIC_FAILING_ASSERTIONS + CONTEXT_FAILING_ASSERTIONS))
    def test_failing_asserts_passthrough(self, assertion_tuple):
        with self._raw_assert('Raises', AssertionError) as context:
            self._run_assertion(assertion_tuple)

        self._raw_assert('NotIsInstance', context.exception, BulkAssertionError)

    @ddt.data(*CONTEXT_PASSING_ASSERTIONS)
    @ddt.unpack
    def test_passing_context_assertion_passthrough(self, assertion, *args):
        assertion_args = []
        args = list(args)

        exception = args.pop(0)

        while not self._is_arg_in_assertion_methods_dict(args[0]):
            assertion_args.append(args.pop(0))

        function = ASSERTION_METHODS_DICT[args.pop(0)]

        with getattr(self, assertion)(exception, *assertion_args):
            function(*args)

    @ddt.data(*CONTEXT_FAILING_ASSERTIONS)
    @ddt.unpack
    def test_failing_context_assertion_passthrough(self, assertion, *args):
        assertion_args = []
        args = list(args)

        exception = args.pop(0)

        while not self._is_arg_in_assertion_methods_dict(args[0]):
            assertion_args.append(args.pop(0))

        function = ASSERTION_METHODS_DICT[args.pop(0)]

        with self._raw_assert('Raises', AssertionError) as context:
            with getattr(self, assertion)(exception, *assertion_args):
                function(*args)

        self._raw_assert('NotIsInstance', context.exception, BulkAssertionError)

    @ddt.data(*list(itertools.product(
        CONTEXT_PASSING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS
    )))
    @ddt.unpack
    def test_bulk_assert(self, passing_assertion, failing_assertion1, failing_assertion2):
        contextmanager = self.bulk_assertions()

        contextmanager.__enter__()
        self._run_assertion(passing_assertion)
        self._run_assertion(failing_assertion1)
        self._run_assertion(failing_assertion2)

        with self._raw_assert('Raises', BulkAssertionError) as context:
            contextmanager.__exit__(None, None, None)

        self._raw_assert('Equals', len(context.exception.errors), 2)

    @ddt.data(*list(itertools.product(
        CONTEXT_FAILING_ASSERTIONS
    )))
    @ddt.unpack
    def test_nested_bulk_asserts(self, failing_assertion):
        with self._raw_assert('Raises', BulkAssertionError) as context:
            with self.bulk_assertions():
                self._run_assertion(failing_assertion)
                with self.bulk_assertions():
                    self._run_assertion(failing_assertion)
                    self._run_assertion(failing_assertion)

        self._raw_assert('Equal', len(context.exception.errors), 3)

    @ddt.data(*list(itertools.product(
        CONTEXT_PASSING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS,
        CONTEXT_FAILING_ASSERTIONS
    )))
    @ddt.unpack
    def test_bulk_assert_closed(self, passing_assertion, failing_assertion1, failing_assertion2):
        with self._raw_assert('Raises', BulkAssertionError) as context:
            with self.bulk_assertions():
                self._run_assertion(passing_assertion)
                self._run_assertion(failing_assertion1)

        self._raw_assert('Equals', len(context.exception.errors), 1)

        with self._raw_assert('Raises', AssertionError) as context:
            self._run_assertion(failing_assertion2)

        self._raw_assert('NotIsInstance', context.exception, BulkAssertionError)
