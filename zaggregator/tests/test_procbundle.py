import unittest
from zaggregator.procbundle import ProcBundle, ProcTable
import psutil
import time
import logging

import zaggregator.utils as utils
import zaggregator.tests as tests

class TestProcBundle(tests.TestCase):
    def test_ProcessBundle_name(self):
        bname = 'unittest-pb'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        bundle = ProcBundle(psutilproc)
        self.assertTrue(bundle.bundle_name == bname)

        bunch.stop()

    # TODO: implement procsort check
    def test_ProcTable_procsort(self):
        try:
            table = ProcTable()
            for b in table.bundles:
                logging.debug("\n{} {}: {}".format(b.bundle_name, b.__class__.__name__, b.proclist))
        except psutil._exceptions.AccessDenied as e:
            logging.error(e)
            logging.error("Some tests require root priveleges")
        logging.debug("Total number of bundles: {}".format(len(table.bundles)))

    def test_ProcTable_get_bundle_names(self):
        try:
            table = ProcTable()
            logging.debug("Bundle names: {}".format(table.get_bundle_names()))
        except psutil._exceptions.AccessDenied as e:
            logging.error(e)
            logging.error("Some tests require root priveleges")


    def test_ProcBundle_append(self):
        bname = 'unittest-pba'
        (bunch, myproc, psutilproc),(bunch2, myproc2, psutilproc2) = \
            tests.BunchProto.start(bname),tests.BunchProto.start(bname)

        bundle,bundle2 = ProcBundle(psutilproc),ProcBundle(psutilproc2)
        bundle = bundle.append(bundle2.proclist[1])

        self.assertTrue(utils.is_proc_in_bundle(bundle2.proclist[1], bundle))

        bunch.stop()
        bunch2.stop()

    def test_ProcBundle_merge(self):
        bname = 'unittest-pbm'
        ((bunch1, myproc1, psutilproc1),(bunch2, myproc2, psutilproc2), (bunch3, myproc3, psutilproc3)) = (tests.BunchProto.start(bname),
                tests.BunchProto.start(bname),
                tests.BunchProto.start(bname))

        bundle1,bundle2,bundle3 = ProcBundle(psutilproc1),ProcBundle(psutilproc2),ProcBundle(psutilproc3)
        bundle1 = bundle1.merge([bundle2,bundle3])

        self.assertTrue(utils.is_proc_in_bundle(bundle2.proclist[1], bundle1))
        self.assertTrue(bundle2.leader[0] in  bundle2.leader)

        bunch1.stop()
        bunch2.stop()
        bunch3.stop()

    def test_ProcBundle_stats(self):
        bname = 'unittest-pbs'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        bundle = ProcBundle(psutilproc)
        self.assertIsInstance(bundle.get_n_connections(), int)
        self.assertIsInstance((bundle.get_n_fds()), int)
        self.assertIsInstance(bundle.get_n_open_files(), int)
        self.assertIsInstance(bundle.get_n_ctx_switches_vol(), int)
        self.assertIsInstance(bundle.get_n_ctx_switches_invol(), int)
        self.assertIsInstance(bundle.get_memory_info_rss(), int)
        self.assertIsInstance(bundle.get_cpu_percent(), float)

        bunch.stop()



if __name__ == '__main__':
    run_test_module_by_name(__file__)
