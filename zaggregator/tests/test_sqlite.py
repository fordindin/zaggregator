import unittest
import logging

import zaggregator.sqlite as sqlite
import zaggregator.tests as tests

class TestSqliteModule(tests.TestCase):

    def test_db(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        print(type(sqlite.db))

if __name__ == '__main__':
    run_test_module_by_name(__file__)
