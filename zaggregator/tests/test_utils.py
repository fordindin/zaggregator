import unittest
from fuzzywuzzy import fuzz, StringMatcher
import psutil
import os, sys
from multiprocessing import Process
import time
import random

import zaggregator.utils as utils
import zaggregator.tests as tests
from zaggregator.procbundle import ProcBundle

class TestFuzzyMatching(tests.TestCase):

    fuzzy_string_sets = ([
        "/usr/sbin/zabbix_agentd -c /etc/zabbix/zabbix_agentd.conf",
        "/usr/sbin/zabbix_agentd: collector [idle 1 sec]",
        "/usr/sbin/zabbix_agentd: listener #1 [waiting for connection]",
        "/usr/sbin/zabbix_agentd: listener #2 [waiting for connection]",
        "/usr/sbin/zabbix_agentd: listener #3 [waiting for connection]",
        "/usr/sbin/zabbix_agentd: active checks #1 [idle 1 sec]",
        ],
        [
            "postgres: checkpointer process",
            "postgres: writer process",
            "postgres: wal writer process",
            "postgres: autovacuum launcher process",
            "postgres: stats collector process",
        ],
        [
            "php-fpm: pool main",
            "php-fpm: pool main",
            "php-fpm: pool main",
            "php-fpm: pool main",
            ],
        )

    fuzzy_string_sets_nomatch = ([
        "/usr/sbin/zabbix_agentd: active checks #1 [idle 1 sec]",
        "postgres: checkpointer process",
        "php-fpm: pool main",
        ],
        [ 'YK1UYU2C: child#0',
          'LCAR8XLT: child#1',
          '6I6P9FKE: child#2',
          '4ZTJ1YEH: child#3',
          '1Y261N7W: child#4',
          'unittest: master',],
        )


    def test_fuzzy_match_seq(self):
        for i in self.fuzzy_string_sets:
            self.assertTrue(utils.fuzzy_sequence_match(i))
        for i in self.fuzzy_string_sets_nomatch:
            self.assertFalse(utils.fuzzy_sequence_match(i))

    def test_fuzzy_match(self):
        for fuzzy_strings in self.fuzzy_string_sets:
            for i in range(len(fuzzy_strings)-1):
                self.assertTrue(utils.fuzzy_match(*fuzzy_strings[i:i+2]))

    def test_fuzzy_namesearch(self):
        r = []
        for s in self.fuzzy_string_sets:
            r.append(utils.reduce_sequence(s))

        r1 = [
            '/usr/sbin/zabbix_agentd',
            'postgres',
            'php-fpm: pool main']

        self.assertTrue(r == r1)

    def test_is_proc_group_parent(self):
        bname = "unittests"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname)

        self.assertTrue(utils.is_proc_group_parent(psutilproc))

        myproc.terminate()

    def test_proc_is_not_group_parent(self):
        bname = "unittests-np"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, israndom=True)

        self.assertFalse(utils.is_proc_group_parent(psutilproc))

        myproc.terminate()

    def test_parent_has_single_child(self):
        bname = "unittest-sc"
        bunch, myproc, psutilproc = tests.bunchproto.start(bname,
                israndom=random.choice((true,false)), nchildren=1)

        self.assertTrue(utils.parent_has_single_child(psutilproc.children()[0]))

        myproc.terminate()

    def test_parent_has_single_child(self):
        bname = "unittest-nsc"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname,
                israndom=random.choice((True,False)), nchildren=2)

        self.assertFalse(utils.parent_has_single_child(psutilproc.children()[0]))

        myproc.terminate()

    def test_parent_has_single_child_false(self):
        bname = "unittest-nscf"
        bunch, myproc, psutilproc = tests.BunchProto.start(bname,
                israndom=random.choice((True,False)), nchildren=1)

        self.assertTrue(utils.parent_has_single_child(psutilproc.children()[0]))

        myproc.terminate()

    def test_parent_has_single_child_init(self):
        # by init I meant any top-level process, it could be systemd, launchctl and so on
        psutilproc = random.choice(psutil.Process(pid=1).children())
        self.assertFalse(utils.parent_has_single_child(psutilproc))

    def test_parent_has_single_child_chain(self):
        bname = "unittest-ch"
        nproc = random.choice([i for i in range(2,10)])
        bunch, myproc, psutilproc = tests.BunchProto.start(bname, nchildren=nproc)

        bundle = ProcBundle(psutilproc)
        self.assertTrue(len(bundle.proclist)+1 > nproc)

        myproc.terminate()



if __name__ == '__main__':
    run_test_module_by_name(__file__)
