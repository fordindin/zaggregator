#!/usr/bin/env python

import psutil
import logging
import os
import time
import zaggregator.utils as utils

DEFAULT_INTERVAL  = 1.0
interpreters = "python", "perl", "bash", "tcsh", "zsh"

class EmptyBundle(Exception): pass


class _BundleCache:
    def __init__(self):
        self.rss = self.vms = self.conns = self.fds = \
                self.ofiles = self.ctx_vol = self.ctx_invol = 0
        self.pcpu = 0.0

    def set_pcpu(self, value):
        self.pcpu = value

    def add(self, proc):
        with proc.oneshot():
            if proc.is_running():
                self.rss += proc.memory_info().rss
                self.vms += proc.memory_info().vms
                #self.conns += len(proc.connections())
                #self.fds += proc.num_fds()
                #self.ofiles += len(proc.open_files())
                self.ctx_vol += proc.num_ctx_switches().voluntary
                self.ctx_invol += proc.num_ctx_switches().involuntary
                # cannot properly cache it
                #self.pcpu += proc.cpu_percent(interval=DEFAULT_INTERVAL)

class ProcBundle:
    def __init__(self, proc):
        """ new ProcBundle from the process
        """
        self._setup()
        self.leader = [ proc ]
        self.append(proc)
        list(map(self.append, proc.children(recursive=True)))
        names = [ p.name() for p in  self.proclist ]
        self._collect_chain()
        self._set_meaningful_leader()

    def _setup(self):
        self._collect_chain_hook = lambda x: True
        self.proclist = []
        self._cache = _BundleCache()

    def _set_meaningful_leader(self):

        def go_top(proc):
            while proc and not utils.is_kernel_thread(proc) and proc in self.proclist:
                proc = proc.parent()
            return proc

        def go_bottom(proc):
            while proc and len(proc.children()) == 1:
                proc = proc.children()[0]
            return proc

        lp = go_bottom(go_top(self.proclist[0]))
        if lp:
            self.leader = [ lp ]
            self.bundle_name = self.name_from_cmdargs(lp)
        #self.bundle_name = utils.reduce_sequence(names)

    @staticmethod
    def name_from_cmdargs(proc):
        cline = proc.cmdline()
        #print("-"*20)
        #print(cline)
        cline = list(filter(lambda x: not x.startswith("-"), cline))

        def not_interpreter(word) -> bool:
            """ singleton for simplier parsing """
            for i in interpreters:
                if word.find(i) > -1:
                    return False
            return True
        items = ":".join(filter(None,filter(not_interpreter, cline)))
        #print(items)
        #items = os.path.basename(items)
        return items


    def append(self, proc):
        self.proclist.append(proc)
        self._cache.add(proc)
        return self

    def merge(self, bundles):
        for bundle in bundles:
            #self.proclist.extend(bundle.proclist)
            list(map(self.append, bundle.proclist))
            self.leader.extend(bundle.leader)
        return self

    def _collect_chain(self):
        """
            private method, shouldn't be used directly
        """
        self._collect_chain_hook(self) # hook for test monkeypatching
        if not self.leader: return

        proc = self.leader[-1]

        while utils.parent_has_single_child(proc):
            if not utils.is_kernel_thread(proc):
                try:
                    proc = proc.parent()
                    if not utils.is_kernel_thread(proc):
                        self.append(proc)
                except psutil.NoSuchProcess:
                    raise utils.ProcessGone
            else: break

    def __str__(self):
        return "{} name={} hash: {:#x}>".format(self.__class__, self.bundle_name, hash(self))

    def get_n_connections(self) -> int:
        return self._cache.conns

    def get_n_fds(self) -> int:
        return self._cache.fds

    def get_n_open_files(self) -> int:
        return self._cache.ofiles

    def get_n_ctx_switches_vol(self) -> int:
        return self._cache.ctx_vol

    def get_n_ctx_switches_invol(self) -> int:
        return self._cache.ctx_invol

    def get_memory_info_rss(self) -> int:
        """
            returns sum of resident memory sizes for process bundle (in KB)
        """
        return self._cache.rss

    def get_memory_info_vms(self) -> int:
        """
            returns sum of virtual memory sizes for process bundle (in KB)
        """
        return self._cache.vms

    def get_cpu_percent(self) -> float:
        return self._cache.pcpu

    def set_cpu_percent(self):
        def f(p) -> float:
            if p.is_running():
                return p.cpu_percent()
            return 0.0
        [ f(p) for p in self.proclist ]
        time.sleep(DEFAULT_INTERVAL)
        times = [ f(p) for p in self.proclist ]
        self._cache.pcpu = sum(times)

class SingleProcess(ProcBundle):
    def __init__(self, proc):
        self._setup()
        self.leader = [ proc ]
        self.append(proc)
        self.proclist = [ proc ]
        self.bundle_name = ""
        #self._collect_chain()

class LeafBundle(SingleProcess):
    def __init__(self, proc):
        super().__init__(proc)
        self._collect_chain()
        #self._set_meaningful_leader()

class ProcessGroup(ProcBundle):
    def __init__(self, pgid, pidlist):
        self._setup()
        pidlist = list(filter(lambda p: psutil.pid_exists(p), pidlist))
        def filter_dead_process(pid):
            if psutil.pid_exists(pid):
                return psutil.Process(pid=pid)
            return None
        list(map(self.append, filter(None, [ filter_dead_process(p) for p in pidlist ])))
        self.leader = []
        if pgid == 0:
            self.bundle_name = "kernel"
        else:
            if len(sorted(pidlist)) > 0:
                self._set_meaningful_leader()
            else:
                raise EmptyBundle
        #self._collect_chain()
        #self._set_meaningful_leader()


class ProcTable:
    def __init__(self):
        self.bundles = []

        pid_gid_map = [ (os.getpgid(p.pid), p.pid) for p in psutil.process_iter() ]
        # first pass just to initialize timers
        [ p.cpu_percent for p in psutil.process_iter() ]
        groups = set([e[0] for e in pid_gid_map])
        for g in groups:
            pids = [ p[1] for p in filter(lambda x: x[0] == g, pid_gid_map) ]
            if len(pids) > 1:
                try:
                    self.bundles.append(ProcessGroup(g, pids))
                except EmptyBundle:
                    pass

        for proc in psutil.process_iter():
            try:
                # do not process already procesed processes ;)
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
            except (psutil.NoSuchProcess, utils.ProcessGone):
                continue

    def bundled(self) -> list:
        ret = []
        for b in self.bundles:
            ret.extend(b.proclist)
        return ret

    def get_bundle_names(self) -> list:
        return [ b.bundle_name for b in self.bundles ]

    def get_bundle_by_name(self, name):
        if name in self.get_bundle_names():
            return list(filter(lambda x: x.bundle_name == name, self.bundles))[0]
        return None

    def get_idle(self, interval=DEFAULT_INTERVAL):
        return psutil.cpu_times_percent(interval=interval).idle
