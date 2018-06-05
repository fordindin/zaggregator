import unittest
import psutil
import time
import logging
import random
import inspect
import signal

import zaggregator.utils as utils
import zaggregator.tests as tests
from zaggregator.procbundle import ProcBundle, ProcTable, ProcessGroup
from zaggregator.tests import cycle

class TestProcBundle(tests.TestCase):
    def test_ProcessBundle_name(self):
        bname = 'unittest-pb'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        bundle = ProcBundle(psutilproc)
        self.assertTrue(bundle.bundle_name == bname)

        bunch.stop()

    # TODO: implement procsort check
    def test_ProcTable_procsort(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        try:
            table = ProcTable()
            for b in table.bundles:
                logging.debug("\n{} {}: {}".format(b.bundle_name, b.__class__.__name__, b.proclist))
        except psutil._exceptions.AccessDenied as e:
            logging.error(e)
            logging.error("Some tests require root priveleges")
        logging.debug("Total number of bundles: {}".format(len(table.bundles)))

    def test_ProcTable_get_bundle_names(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        try:
            table = ProcTable()
            logging.debug("Bundle names: {}".format(table.get_bundle_names()))
        except psutil._exceptions.AccessDenied as e:
            logging.error(e)
            logging.error("Some tests require root priveleges")


    def test_ProcBundle_append(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        bname = 'unittest-pba'
        (bunch, myproc, psutilproc),(bunch2, myproc2, psutilproc2) = \
            tests.BunchProto.start(bname),tests.BunchProto.start(bname)

        bundle,bundle2 = ProcBundle(psutilproc),ProcBundle(psutilproc2)
        bundle = bundle.append(bundle2.proclist[1])

        self.assertTrue(utils.is_proc_in_bundle(bundle2.proclist[1], bundle))

        bunch.stop()
        bunch2.stop()

    def test_ProcBundle_merge(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        bname = 'unittest-pbm'
        ((bunch1, myproc1, psutilproc1),(bunch2, myproc2, psutilproc2), (bunch3, myproc3, psutilproc3)) = (tests.BunchProto.start(bname),
                tests.BunchProto.start(bname),
                tests.BunchProto.start(bname))

        bundle1,bundle2,bundle3 = ProcBundle(psutilproc1),ProcBundle(psutilproc2),ProcBundle(psutilproc3)
        logging.debug(len(bundle1.proclist))
        bundle1.merge([bundle2,bundle3])
        logging.debug(len(bundle1.proclist))


        self.assertTrue(utils.is_proc_in_bundle(bundle2.proclist[1], bundle1))
        self.assertTrue(bundle2.leader[0] in  bundle2.leader)

        bunch1.stop()
        bunch2.stop()
        bunch3.stop()

    def test_ProcBundle_stats(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
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

    def test_Procbundle_nopid(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        bname = 'unittest-np'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        bundle = ProcBundle(psutilproc)
        rpid = random.randint(0, 1024)
        while psutil.pid_exists(rpid):
            rpid = random.randint(0, 1024)
        pidlist = [ p.pid for p in psutilproc.children() ]
        pgid = psutilproc.pid
        pidlist.append(rpid)

        bundle = ProcessGroup(pgid, pidlist)
        self.assertIsInstance(bundle, ProcessGroup)

        bunch.stop()

    def test_get_idle(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        p = ProcTable()
        self.assertIsInstance(p.get_idle(interval=0.1), float)


    def test_get_pcpu_busy(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])

        bname = "unittest-gpcpb"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=2, func=cycle)
        p = ProcTable()
        bundle = p.get_bundle_by_name("test.sh")
        bundle.set_cpu_percent()
        self.assertTrue(bundle.get_cpu_percent() > 90)
        #print(bundle.get_cpu_percent())

        bunch.stop()


if __name__ == '__main__':
    run_test_module_by_name(__file__)
