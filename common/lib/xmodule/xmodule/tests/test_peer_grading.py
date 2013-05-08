import unittest
from xmodule.modulestore import Location
import json
from lxml import etree
from mock import Mock
from . import test_system
from dummy_system import DummySystem, DummySystemUser

from xmodule.peer_grading_module import PeerGradingModule, PeerGradingDescriptor
from xmodule.open_ended_grading_classes.grading_service_module import GradingServiceError

ORG = "edX"
COURSE="open_ended"


class PeerGradingModuleTest(unittest.TestCase, DummySystemUser):
    location = Location(["i4x", "edX", "open_ended", "peergrading",
                         "SampleQuestion"])
    max_score = 1

    definition = "<peergrading/>"
    descriptor = Mock(data=definition)

    def setUp(self):
        self.test_system = test_system()
        self.test_system.open_ended_grading_interface = None
        self.peer_grading = PeerGradingModule(self.test_system, self.location,self.descriptor, model_data={'data': self.definition})

    def test_module_closed(self):
        closed = self.peer_grading.closed()
        self.assertEqual(closed, False)

    def test_get_html(self):
        html = self.peer_grading.get_html()

    def test_get_data(self):
        try:
            success, data = self.peer_grading.query_data_for_location()
        except GradingServiceError:
            pass

    def test_get_score(self):
        score = self.peer_grading.get_score()

    def test_get_max_score(self):
        max_score = self.peer_grading.max_score()

    def get_next_submission(self):
        success, next_submission = self.peer_grading.get_next_submission({'location' : 'blah'})