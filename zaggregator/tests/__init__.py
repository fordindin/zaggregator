import unittest
import os
import logging as log
import random
import psutil
import string
import os, time
import sys
from multiprocessing import Process

VERBOSITY = 2
HERE = os.path.abspath(os.path.dirname(__file__))

class TestCase(unittest.TestCase):

    # Print a full path representation of the single unit tests
    # being run.
    def __str__(self):
        return "%s.%s.%s" % (
            self.__class__.__module__, self.__class__.__name__,
            self._testMethodName)

    # assertRaisesRegexp renamed to assertRaisesRegex in 3.3;
    # add support for the new name.
    if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
        assertRaisesRegex = unittest.TestCase.assertRaisesRegexp

# override default unittest.TestCase
unittest.TestCase = TestCase

LOGFILE="test.log"
log.basicConfig(filename=LOGFILE, level=log.DEBUG)
print("Unittest log stored at {}".format(os.path.realpath(LOGFILE)))

class BunchProto:

    sleeptime = 5.0
    ttime = 0.1

    def __init__(self, name="defname", israndom=False, nchildren=5, rstrlen=8, func=None):
        self.nchildren = nchildren
        self.rstrlen = rstrlen
        self.name = name
        self.israndom = israndom
        self.master = Process(target=self.process_proto_parent)
        self.psutilproc = None
        self.func = func

    def name_or_random(self, i):
        name = self.name
        if self.israndom:
            name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in
                    range(self.rstrlen))
        return "{}: child#{!s}".format(name, i)

    @staticmethod
    def process_proto(name, sleeptime, func):
        import setproctitle
        setproctitle.setproctitle(name)

        if func or not sleeptime:
            func()
        else:
            time.sleep(BunchProto.sleeptime)

    def process_proto_parent(self):
        import setproctitle
        import signal
        import sys

        def sig_mitigator(signum, frame):
            def _stop(p):
                class fake_fd:
                    def terminate(self):
                        pass
                if p._popen == None:
                    p._popen = fake_fd()
                p.terminate()
            [ _stop(p) for p in self.pcs ]
            sys.exit(0)

        signal.signal(signal.SIGTERM, sig_mitigator)

        setproctitle.setproctitle("{}: master".format(self.name))
        self.pcs = [ Process(target=BunchProto.process_proto,
            args=(self.name_or_random(i), self.sleeptime, self.func)) for i in range(self.nchildren) ]
        [ p.start() for p in self.pcs ]

    @staticmethod
    def start(name, israndom=False, nchildren=5, rstrlen=8, func=None ):
        bunch = BunchProto(name, israndom=israndom, nchildren=nchildren, rstrlen=rstrlen,
                func=func)
        myproc = bunch.master
        myproc.start()
        time.sleep(BunchProto.ttime) # give process a moment to set it's title properly
        psutilproc = psutil.Process(pid=myproc.pid)
        bunch.psutilproc = psutilproc
        return bunch,myproc,psutilproc

    def stop(self):
        def _stop(p):
            if p.is_running():
                p.terminate()
        [ _stop(p) for p in psutil.Process(pid=self.master.pid).children() ]
        if psutil.Process(pid=self.master.pid).is_running():
            self.master.terminate()

def cycle():
    # singleton, which does nothing, only consumes CPU
    import signal
    import sys

    def sig_mitigator(signum, frame):
        sys.exit(0)

    # define and install custom SIGTERM handler
    signal.signal(signal.SIGTERM, sig_mitigator)

    while True:
        pass

def get_suite():
    testmods = [os.path.splitext(x)[0] for x in os.listdir(HERE)
                if x.endswith('.py') and x.startswith('test_') and not
                x.startswith('test_memory_leaks')]
    if "WHEELHOUSE_UPLOADER_USERNAME" in os.environ:
        testmods = [x for x in testmods if not x.endswith((
                    "osx", "posix", "linux"))]
    suite = unittest.TestSuite()
    for tm in testmods:
        # ...so that the full test paths are printed on screen
        tm = "zaggregator.tests.%s" % tm
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(tm))
    return suite

def run_suite():
    _setup_tests()
    result = unittest.TextTestRunner(verbosity=VERBOSITY).run(get_suite())
    success = result.wasSuccessful()
    sys.exit(0 if success else 1)

def _setup_tests():
    pass

def run_test_module_by_name(name):
    testmodules = [os.path.splitext(x)[0] for x in os.listdir(HERE)
                    if x.endswith('.py') and x.startswith('test_')]
    _setup_tests()
    name = os.path.splitext(os.path.basename(name))[0]
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(name))
    result = unittest.TextTestRunner(verbosity=VERBOSITY).run(suite)
    success = result.wasSuccessful()
    sys.exit(0 if success else 1)
