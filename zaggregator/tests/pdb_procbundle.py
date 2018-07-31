#!/usr/bin/env python3
import zaggregator
import zaggregator.utils as utils
import zaggregator.tests as tests
import zaggregator.procbundle as pb
from zaggregator.procbundle import ProcBundle
from zaggregator.proctable import ProcTable
from zaggregator.procmirror import ProcessMirror
from zaggregator.tests import cycle

if __name__ == '__main__':
    pt = ProcTable()
    for p in pt._procs:
        print(p)
