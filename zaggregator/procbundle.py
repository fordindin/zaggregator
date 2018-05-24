#!/usr/bin/env python

import psutil
import logging
import os
import zaggregator.utils as utils

class ProcBundle:
    def __init__(self, proc):
        """ new ProcBundle from the process
        """
        self.leader = [ proc ]
        self.proclist = [ proc ]
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
        if len(self.bundle_name) < 3:
            self.bundle_name = "{}:{}".format(self.proclist[0].username(),names[0])
        self._collect_chain()

    def append(self, proc):
        self.proclist.append(proc)
        return self

    def merge(self, bundles):
        for bundle in bundles:
            self.proclist.extend(bundle.proclist)
            self.leader.extend(bundle.leader)
        return self

    def _collect_chain(self):
        """
            private method, shouldn't be used directly
        """
        if not self.leader: return

        proc = self.leader[-1]

        while utils.parent_has_single_child(proc):
            proc = proc.parent()
            if not utils.is_kernel_thread(proc):
                self.proclist.append(proc)

    def __str__(self):
        return "{} name={} hash: {:#x}>".format(self.__class__, self.bundle_name, hash(self))

class SingleProcess(ProcBundle):
    def __init__(self, proc):
        self.leader = [ proc ]
        self.proclist = [ proc ]
        self.bundle_name = proc.name()

class LeafBundle(SingleProcess):
    def __init__(self, proc):
        super().__init__(proc)
        self._collect_chain()

class ProcessGroup(ProcBundle):
    def __init__(self, pgid, pidlist):
        self.proclist = [ psutil.Process(pid=p) for p in pidlist ]
        self.leader = []
        if pgid == 0:
            self.bundle_name = "kernel"
        else:
            self.leader = [psutil.Process(pid=sorted(pidlist)[0])]
            self.bundle_name = self.leader[0].name()


class ProcTable:
    def __init__(self):
        self.bundles = []

        pid_gid_map = [ (os.getpgid(p.pid), p.pid) for p in psutil.process_iter() ]
        groups = set([e[0] for e in pid_gid_map])
        for g in groups:
            pids = [ p[1] for p in filter(lambda x: x[0] == g, pid_gid_map) ]
            if len(pids) > 1:
                self.bundles.append(ProcessGroup(g, pids))

        for proc in psutil.process_iter():
            # do not process process groups
            if proc in self.bundled(): continue

            # collect bundleable processes
            if utils.is_proc_group_parent(proc) and (proc not in self.bundled()):
                self.bundles.append(ProcBundle(proc))
                continue

            # collect leaf process chains
            if utils.is_leaf_process(proc):
                self.bundles.append(LeafBundle(proc))
                continue

            # all non-categorized processes are SingleProcess
            self.bundles.append(SingleProcess(proc))

            # merge similar bundles

            merged = []
            for bundle in self.bundles:
                if bundle in merged: continue
                if bundle.bundle_name == 'kernel': continue
                similar = [val for i,val in enumerate(self.bundles) if val.bundle_name==bundle.bundle_name]
                # if there more than one bundle with same name
                if len(similar) > 1:
                    similar[0].merge(similar[1:])
                    merged.extend(similar)
            for b in merged:
                self.bundles.remove(b)

    def bundled(self) -> list:
        ret = []
        for b in self.bundles:
            ret.extend(b.proclist)
        return ret

    def get_bundle_names(self) -> list:
        return [ b.bundle_name for b in self.bundles ]

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
