import unittest

from partitions import Group, UserPartition


class Test_Group(unittest.TestCase):

    def test_construct(self):
        id = "an_id"
        name = "Grendel"
        g = Group(id, name)
        self.assertEqual(g.id, id)
        self.assertEqual(g.name, name)

    def test_to_json(self):
        id = "an_id"
        name = "Grendel"
        g = Group(id, name)
        jsonified = g.to_json()
        self.assertEqual(jsonified, {"id": id,
                                     "name": name,
                                     "version": g.VERSION})

    def test_from_json(self):
        id = "an_id"
        name = "Grendel"
        jsonified = {"id": id,
                     "name": name,
                     "version": Group.VERSION}
        g = Group.from_json(jsonified)
        self.assertEqual(g.id, id)
        self.assertEqual(g.name, name)

