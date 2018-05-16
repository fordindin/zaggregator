#!/usr/bin/env python

import psutil
import sys
import logging
from fuzzywuzzy import fuzz
import utils
from procbundle import ProcTable

"""
There is phases of processing:

    1) look through process table processes with number of children (which are childless).
    Processes should have a name similar in that process group (represented as ProcBunch
    class)
"""

"""
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__',
'__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__',
'__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
'__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_create_time',
'_exe', '_gone', '_hash', '_ident', '_init', '_last_proc_cpu_times',
'_last_sys_cpu_times', '_name', '_oneshot_inctx', '_pid', '_ppid', '_proc',
'_send_signal', 'as_dict', 'children', 'cmdline', 'connections', 'cpu_affinity',
'cpu_num', 'cpu_percent', 'cpu_times', 'create_time', 'cwd', 'environ', 'exe', 'gids',
'io_counters', 'ionice', 'is_running',
'kill', 'memory_full_info', 'memory_info', 'memory_info_ex', 'memory_maps',
'memory_percent', 'name', 'nice', 'num_ctx_switches', 'num_fds', 'num_threads', 'oneshot',
'open_files', 'parent', 'pid', 'ppid', 'resume', 'rlimit', 'send_signal', 'status',
'suspend', 'terminal', 'terminate', 'threads', 'uids', 'username', 'wait']
"""


pt = ProcTable()
