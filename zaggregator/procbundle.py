#!/usr/bin/env python

import psutil
import logging
import zaggregator.utils as utils

class ProcBundle:
    def __init__(self, proc):
        """ new ProcBundle from the process
        """
        self.proclist = [proc]
        self.proclist.extend(proc.children())
        self.bundle_name = "" # wil be overwritten later

    def similar_to(self, proc):
        pass

class ProcTable:
    def __init__(self):
        self.bundles = []
        for proc in psutil.process_iter():
            with proc.oneshot():
                if utils.is_proc_group_parent(proc):
                    self.bundles.append(ProcBundle(proc))
        print(self.bundles)

        """
                children_names = [ p.name() for p in proc.children() ]
                if proc.cmdline() and proc.cmdline()[0] == '/usr/sbin/zabbix_agentd':
                    print(proc.cmdline())
                    print(proc.connections())
                    print(proc.num_fds())
                    print(proc.memory_info())
                    print(proc.cpu_percent())
                    print(proc.create_time())
                    print(proc.open_files())
                    print(proc.parent())
                    print(proc.num_ctx_switches())
                    print(children_names)
                    print(proc.cwd())
                    sys.exit(0)
                    """
