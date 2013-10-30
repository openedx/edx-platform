""" User script for load testing CustomResponse """

from capa.tests.response_xml_factory import CustomResponseXMLFactory
import capa.capa_problem as lcp
from xmodule.x_module import ModuleSystem
import mock
import fs.osfs
import random
import textwrap

# Use memcache running locally
CACHE_SETTINGS = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211'
    },
}

# Configure settings so Django will let us import its cache wrapper
# Caching is the only part of Django being tested
from django.conf import settings
settings.configure(CACHES=CACHE_SETTINGS)

from django.core.cache import cache

# Script to install as the checker for the CustomResponse
TEST_SCRIPT = textwrap.dedent("""
        def check_func(expect, answer_given):
            return {'ok': answer_given == expect, 'msg': 'Message text'}
""")

# Submissions submitted by the student
TEST_SUBMISSIONS = [random.randint(-100, 100) for i in range(100)]


class TestContext(object):
    """ One-time set up for the test that is shared across transactions.
    Uses a Singleton design pattern."""

    SINGLETON = None
    NUM_UNIQUE_SEEDS = 20

    @classmethod
    def singleton(cls):
        """ Return the singleton, creating one if it does not already exist."""

        # If we haven't created the singleton yet, create it now
        if cls.SINGLETON is None:

            # Create a mock ModuleSystem, installing our cache
            system = mock.MagicMock(ModuleSystem)
            system.STATIC_URL = '/dummy-static/'
            system.render_template = lambda template, context: "<div>%s</div>" % template
            system.cache = cache
            system.filestore = mock.MagicMock(fs.osfs.OSFS)
            system.filestore.root_path = ""
            system.DEBUG = True

            # Create a custom response problem
            xml_factory = CustomResponseXMLFactory()
            xml = xml_factory.build_xml(script=TEST_SCRIPT, cfn="check_func", expect="42")

            # Create and store the context
            cls.SINGLETON = cls(system, xml)

        else:
            pass

        # Return the singleton
        return cls.SINGLETON

    def __init__(self, system, xml):
        """ Store context needed for the test across transactions """
        self.system = system
        self.xml = xml

        # Construct a small pool of unique seeds
        # To keep our implementation in line with the one capa actually uses,
        # construct the problems, then use the seeds they generate
        self.seeds = [lcp.LoncapaProblem(self.xml, 'problem_id', system=self.system).seed
                      for i in range(self.NUM_UNIQUE_SEEDS)]

    def random_seed(self):
        """ Return one of a small number of unique random seeds """
        return random.choice(self.seeds)

    def student_submission(self):
        """ Return one of a small number of student submissions """
        return random.choice(TEST_SUBMISSIONS)


class Transaction(object):
    """ User script that submits a response to a CustomResponse problem """

    def __init__(self):
        """ Create the problem """

        # Get the context (re-used across transactions)
        self.context = TestContext.singleton()

        # Create a new custom response problem
        # using one of a small number of unique seeds
        # We're assuming that the capa module is limiting the number
        # of seeds (currently not the case for certain settings)
        self.problem = lcp.LoncapaProblem(
            self.context.xml, '1',
            state=None, seed=self.context.random_seed(),
            system=self.context.system,
        )

    def run(self):
        """ Submit a response to the CustomResponse problem """
        answers = {'1_2_1': self.context.student_submission()}
        self.problem.grade_answers(answers)

if __name__ == '__main__':
    trans = Transaction()
    trans.run()
