import unittest
import psutil
import time
import logging
import random
import inspect
import signal
import os

import zaggregator
import zaggregator.utils as utils
import zaggregator.tests as tests
import zaggregator.procbundle as pb
from zaggregator.procbundle import ProcBundle, ProcTable, ProcessMirror
from zaggregator.tests import cycle

zaggregator.procbundle.DEFAULT_INTERVAL=0.1

class TestProcMirror(tests.TestCase):
    def test_ProcessMirror_alive(self):
        proc = psutil.Process(pid=os.getpid())
        mirror = ProcessMirror(proc, None)
        self.assertTrue(mirror.alive)
        self.assertTrue(mirror.alive == proc.is_running())

    def test_ProcessMirror_pid(self):
        proc = psutil.Process(pid=os.getpid())
        mirror = ProcessMirror(proc, None)
        self.assertTrue(mirror.pid == proc.pid == os.getpid())

    def test_ProcessMirror_set_pcpu(self):
        proc = psutil.Process(pid=os.getpid())
        mirror = ProcessMirror(proc, None)
        mirror.set_pcpu(0.123456)
        self.assertTrue(mirror.pcpu == 0.123456)

class TestProcTable(tests.TestCase):
    def test_ProcTable_mirror_by_pid(self):
        pt = ProcTable()
        proc = psutil.Process(pid=os.getpid())
        self.assertTrue(pt.mirror_by_pid(os.getpid()).pid == os.getpid() )

    def test_ProcTable_mirrors_by_pgid(self):
        bname = 'unittest-ptmbp'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)
        pt = ProcTable()
        pgid = os.getpgid(psutilproc.pid)
        self.assertTrue(
                len(
                    list(filter(None, [ p._pgid != pgid for p in pt.mirrors_by_pgid(pgid)]))
                    ) == 0
                )

        bunch.stop()

    def test_ProcTable_mirror_by_pid(self):
        bname = 'unittest-ptmbp2'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)
        pt = ProcTable()
        self.assertIsInstance(pt.mirror_by_pid(psutilproc.pid), ProcessMirror)

        bunch.stop()

    def test_ProcTable_pidm(self):
        bname = 'unittest-pm'
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)
        pt = ProcTable()
        self.assertIsInstance(pt.mirror_by_pid(psutilproc.pid).pidm(psutilproc.pid), ProcessMirror)

        bunch.stop()

    def test_ProcTable_children(self):
        bname = 'unittest-pm'
        nchildren = 5
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=5)
        pt = ProcTable()
        m = pt.mirror_by_pid(psutilproc.pid)
        self.assertTrue(len(m.children()) == nchildren)
        self.assertIsInstance(m.children()[0], ProcessMirror)

        bunch.stop()

    def test_ProcTable_test(self):
        bname = 'unittest-t'
        nchildren = 5
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=5)
        pt = ProcTable()

        #print(pt.bundles[0].bundle_name)

        bunch.stop()

if __name__ == '__main__':
    tests.run_test_module_by_name(__file__)
