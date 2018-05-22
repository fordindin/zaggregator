#!/usr/bin/env python

import psutil
import logging
import os
import zaggregator.utils as utils

class ProcBundle:
    def __init__(self, proc):
        """ new ProcBundle from the process
        """
        self.leader = proc
        self.proclist = [proc]
        self.proclist.extend(proc.children())
        names = []
        if os.uname().sysname == 'Darwin':
            for p in self.proclist:
                try:
                    names.append(p.cmdline()[0])
                except (psutil._exceptions.AccessDenied, IndexError,
                        psutil.ProcessLookupError, psutil.AccessDenied):
                    pass
        else:
            names = [ p.name() for p in  self.proclist ]
        self.bundle_name = utils.reduce_sequence(names)
        self._collect_chain()

    def _collect_chain(self):
        """
            private method, shouldn't be used directly
        """
        proc = self.leader
        while utils.parent_has_single_child(proc):
            proc = proc.parent()
            if not utils.is_kernel_thread(proc):
                self.proclist.append(proc)

    def __str__(self):
        return "<{} name={} object at {:#x}>".format(self.__class__, self.bundle_name, hash(self))

class LeafBundle(ProcBundle):
    def __init__(self, proc):
        self.leader = proc
        self.proclist = [ proc ]
        self.bundle_name = proc.name()
        self._collect_chain()

class ProcTable:
    def __init__(self):
        self.bundles = []
        for proc in psutil.process_iter():
            # ignore kernel processes
            if utils.is_kernel_thread(proc): continue

            # collect bundleable processes
            if utils.is_proc_group_parent(proc) and (proc not in self.bundled()):
                self.bundles.append(ProcBundle(proc))
                continue

            # collect leaf process chains
            if utils.is_leaf_process(proc):
                self.bundles.append(LeafBundle(proc))




    def bundled(self) -> list:
        ret = []
        for b in self.bundles:
            ret.extend(b.proclist)
        return ret

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
