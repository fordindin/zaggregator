import unittest
import logging
import inspect
import sqlite3

import zaggregator.sqlite as sqlite
sqlite.DBPATH = ":memory:"
sqlite.__init__()
import zaggregator.tests as tests


class TestSqliteModule(tests.TestCase):

    records = (
            ("test0", 1, 2, 10, 41, 10.0),
            ("test1", 5, 2, 11, 42, 11.0),
            ("test2", 6, 8, 13, 43, 12.0),
            ("test3", 7, 9, 12, 44, 13.0),
            )

    def test_db(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        self.assertTrue(type(sqlite.db) == sqlite3.Connection)

    def test_add_get_record(self):
        for r in self.records:
            sqlite.add_record(r)

    def test_get_bundle_names(self):
        names = sqlite.get_bundle_names()
        self.assertTrue(names == [ r[0] for r in self.records ])


if __name__ == '__main__':
    run_test_module_by_name(__file__)
