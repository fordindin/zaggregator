import unittest
from zaggregator.procbundle import ProcBundle, ProcTable
import psutil
import time
import logging

import zaggregator.utils as utils
import zaggregator.tests as tests

class TestProcBundle(tests.TestCase):
    def test_ProcessBundle_name(self):
        bname = 'unittest-procbundle'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        bundle = ProcBundle(psutilproc)
        self.assertTrue(bundle.bundle_name == bname)

        myproc.terminate()

    def test_ProcTable_procsort(self):
        try:
            table = ProcTable()
        except psutil._exceptions.AccessDenied as e:
            logging.error(e)
            logging.error("Some tests require root priveleges")

if __name__ == '__main__':
    run_test_module_by_name(__file__)
