import unittest
import os
import logging as log
import logging as log
import random
import string
import os, time
from multiprocessing import Process

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

def bunch_proto(name="", israndom=False):
    def name_or_random(i, name, israndom):
        oname = name
        if israndom:
            oname = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        return "{}: child#{!s}".format(oname, i)

    def process_proto(name, sleeptime):
        import setproctitle
        setproctitle.setproctitle(name)
        time.sleep(sleeptime)

    def process_proto_parent(name, sleeptime, israndom):
        import setproctitle
        setproctitle.setproctitle("{}: master".format(name))
        pcs = [ Process(target=process_proto, args=(name_or_random(i, name, israndom), sleeptime)) for i in range(5) ]
        [ p.start() for p in pcs ]

    sleeptime = 5.0
    return Process(target=process_proto_parent, args=(name, sleeptime, israndom))

def run_suite():
    _setup_tests()
    result = unittest.TextTestRunner(verbosity=VERBOSITY).run(get_suite())
    success = result.wasSuccessful()
    sys.exit(0 if success else 1)

def run_test_module_by_name(name):
    # testmodules = [os.path.splitext(x)[0] for x in os.listdir(HERE)
    #                if x.endswith('.py') and x.startswith('test_')]
    _setup_tests()
    name = os.path.splitext(os.path.basename(name))[0]
    suite = unittest.TestSuite()
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName(name))
    result = unittest.TextTestRunner(verbosity=VERBOSITY).run(suite)
    success = result.wasSuccessful()
    sys.exit(0 if success else 1)
