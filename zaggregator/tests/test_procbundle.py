import unittest
import psutil
import time
import logging
import random
import inspect
import signal

import zaggregator
import zaggregator.utils as utils
import zaggregator.tests as tests
import zaggregator.procbundle as pb
from zaggregator.procbundle import ProcBundle, ProcTable, ProcessMirror
from zaggregator.tests import cycle
zaggregator.procbundle.DEFAULT_INTERVAL=0.1

class TestProcBundle(tests.TestCase):

    def test_ProcessBundle_name(self):
        bname = 'unittest-pb'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        procs = psutilproc.children()
        procs.append(psutilproc)
        pt = ProcTable()
        procs = [ ProcessMirror(p,pt) for p in procs ]
        bundle = ProcBundle(procs, pt=pt)
        print(bundle.bundle_name)
        self.assertTrue(bundle.bundle_name == bname)

        bunch.stop()

    def test_ProcTable_get_bundle_names(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        try:
            table = ProcTable()
            logging.debug("Bundle names: {}".format(table.get_bundle_names()))
        except psutil._exceptions.AccessDenied as e:
            logging.error(e)
            logging.error("Some tests require root priveleges")

    """

    def test_ProcBundle_merge(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        bname = 'unittest-pbm'
        ((bunch1, myproc1, psutilproc1),(bunch2, myproc2, psutilproc2), (bunch3, myproc3, psutilproc3)) = (tests.BunchProto.start(bname),
                tests.BunchProto.start(bname),
                tests.BunchProto.start(bname))

        pt = ProcTable()
        bundle1,bundle2,bundle3 = ( ProcBundle([ProcessMirror(psutilproc1, pt)]),
                ProcBundle([ProcessMirror(psutilproc2, pt)]),
                ProcBundle([ProcessMirror(psutilproc3, pt)]) )
        logging.debug(len(bundle1.proclist))
        bundle1.merge(bundle2)
        bundle1.merge(bundle3)
        logging.debug(len(bundle1.proclist))


        self.assertTrue(utils.is_proc_in_bundle(bundle2.proclist[1], bundle1))
        self.assertTrue(bundle2.leader[0] in  bundle2.leader)

        bunch1.stop()
        bunch2.stop()
        bunch3.stop()

    """
    def test_ProcBundle_stats(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        bname = 'unittest-pbs'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        pt = ProcTable()
        bundle = pt.get_bundle_by_name(pt.get_bundle_names()[0])
        self.assertIsInstance(bundle.get_n_ctx_switches_vol(), int)
        self.assertIsInstance(bundle.get_n_ctx_switches_invol(), int)
        self.assertIsInstance(bundle.get_memory_info_rss(), int)
        self.assertIsInstance(bundle.get_memory_info_vms(), int)
        self.assertIsInstance(bundle.get_cpu_percent(), float)

        bunch.stop()

    def test_get_idle(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])
        p = ProcTable()
        self.assertIsInstance(p.get_idle(), float)

        bname = "unittest-gi"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=2, func=cycle)
        p = ProcTable()

        self.assertTrue(p.get_idle() < 10.0)

        bunch.stop()

    def test_get_pcpu_busy(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])

        bname = "unittest-gpcpb"
        procname = "sh:./test.sh"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=2, func=cycle)
        p = ProcTable()
        time.sleep(0.1)
        #print(p.get_bundle_names())
        """
        for b in p.bundles:
            print("{}:\t{}".format(b.bundle_name, b.proclist))
        """
        bundle = p.get_bundle_by_name(bname)
        pcpu = bundle.get_cpu_percent()
        #print(bundle.__class__)
        pcpu_threshold = 75
        if pcpu <= pcpu_threshold:
            print("pcpu value: {}".format(pcpu))
        self.assertTrue(pcpu > pcpu_threshold)


        bunch.stop()

    def test_name_from_proctitles(self):
        logging.debug("======= %s ======" % inspect.stack()[0][3])

        bname = "unittest-nfpt"
        procname = "sh:./test.sh"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=2, func=cycle)
        p = ProcTable()
        time.sleep(0.1)
        bundle = p.get_bundle_by_name(bname)
        print(bundle._name_from_self_proclist())
        bunch.stop()
        """
    """

if __name__ == '__main__':
    run_test_module_by_name(__file__)
