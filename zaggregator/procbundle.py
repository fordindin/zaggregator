#!/usr/bin/env python

import psutil
import logging
import os
import time
import zaggregator.utils as utils

DEFAULT_INTERVAL  = 1.0
interpreters = "python", "perl", "bash", "tcsh", "zsh"

class ProcessMirror:
    def __init__(self, proc, proctable):
        self._proc, self._pt = proc, proctable
        parent = proc.parent()
        if parent:
            self._parent = parent.pid
        else:
            self._parent = 0
        self._children = [ p.pid for p in proc.children() ]
        self._pgid = os.getpgid(proc.pid)

        with proc.oneshot():
            if proc.is_running():
                self.rss = proc.memory_info().rss
                self.vms = proc.memory_info().vms
                self.ctx_vol = proc.num_ctx_switches().voluntary
                self.ctx_invol = proc.num_ctx_switches().involuntary
                self._cmdline = proc.cmdline()
                self.pcpu = None
                #self.pcpu += proc.cpu_percent(interval=DEFAULT_INTERVAL)
            else: self = None

    def __str__(self):
        return "<{} name={} pid={} _pgid={} alive={} >\n".format(self.__class__.__name__,
                self.name(), self.pid,
                self._pgid, self.alive)

    def __repr__(self):
        return self.__str__()

    def __getattribute__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        elif name == "alive":
            return self._proc.is_running()
        elif name == "pidm":
            def __wrapper(x):
                try:
                    return self._pt.mirrors[x]
                except KeyError:
                    return False
            return __wrapper
        elif name == "parent":
            return lambda: self.pidm(self._parent)
        elif name == "children":
            return lambda: [ self.pidm(p) for p in self._children ]
        elif name == "cmdline":
            return lambda: self._cmdline
        elif hasattr(self._proc, name):
            return getattr(self._proc, name)
        else:
            return object.__getattribute__(self, name)

    def set_pcpu(self, value):
        self.pcpu = value

class EmptyBundle(Exception): pass

class ProcBundle:
    def __init__(self, proclist, pt=None):

        self.proctable = pt

        if isinstance(proclist, ProcessMirror):
            self._pgid = proclist._pgid
            self.proclist = [ proclist ]

        if isinstance(proclist, list):
            self._pgid = proclist[0]._pgid
            self.proclist = proclist
            if len(proclist) == 0:
                raise EmptyBundle

        if isinstance(proclist, psutil.Process):
            self._pgid = os.getpgid(proclist.pid)
            self.proclist = [ proclist ]

        proc = self.proclist[0]
        self.leader = proc

        while utils.parent_has_single_child(proc):
            if not utils.is_kernel_thread(proc):
                proc = proc.parent()
                if proc and not utils.is_kernel_thread(proc) and proc not in self.proctable.bundled():
                    self.append(proc)
                    self.proctable._clear_expendable()
            else: break

        def go_top(proc):
            while proc and not utils.is_kernel_thread(proc):
                proc = proc.parent()
            return proc

        def go_bottom(proc):
            if not proc:
                return proc
            while not (proc._pgid == self._pgid or len(proc.children()) > 1):
                children = proc.children()
                if len(children) > 0:
                    proc = children[0]
                else:
                    return proc
            return proc

        lp = go_bottom(go_top(self.proclist[0]))

        if lp:
            self.leader = lp
            self.bundle_name = self.name_from_cmdargs(lp)
            children_pids = [ p.pid for p in lp._proc.children(recursive=True) ]
            for p in children_pids:
                mirror = self.proctable.mirror_by_pid(p)
                if mirror not in self.proctable.bundled():
                    self.append(mirror)
        else:
            self.bundle_name = self.name_from_cmdargs(self.leader)

    def append(self, proc):
        self.proclist.append(proc)

    def merge(self, bundle):
        self.proclist.extend(bundle.proclist)
        self.proctable.bundles.remove(bundle)

    @staticmethod
    def name_from_cmdargs(proc):
        if utils.is_kernel_thread(proc): return "kernel"
        cline = list(filter(lambda x: not x.startswith("-"), proc.cmdline()))

        def not_interpreter(word) -> bool:
            """ singleton for simplier parsing """
            for i in interpreters:
                if word.find(i) > -1:
                    return False
            return True

        if cline and cline[0].startswith("/"):
            cline[0] =  os.path.basename(cline[0])
        out = ":".join(filter(None,filter(not_interpreter, cline)))
        try:
            out.split()[0].strip(":")
        except IndexError:
            return os.path.basename(proc.cmdline()[0])
        return out.split()[0].strip(":")[:20]

    def get_n_ctx_switches_vol(self) -> int:
        return sum([p.ctx_vol for p in  self.proclist])

    def get_n_ctx_switches_invol(self) -> int:
        return sum([p.ctx_invol for p in  self.proclist])

    def get_memory_info_rss(self) -> int:
        """
            returns sum of resident memory sizes for process bundle (in KB)
        """
        return sum([p.rss for p in  self.proclist])

    def get_memory_info_vms(self) -> int:
        """
            returns sum of virtual memory sizes for process bundle (in KB)
        """
        return sum([p.vms for p in  self.proclist])

    def get_cpu_percent(self) -> float:
        return sum([p.pcpu for p in  self.proclist])


# singleton to filter-out dead processes
def alive_or_false(proc):
    if proc.is_running():
        return proc
    return False

def process_call_guard(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except psutil.NoSuchProcess:
        return False

class ProcTable:
    def __init__(self):
        self._procs = []
        # fill the self._procs with ProcessMirrors of psutil processes
        _pcs = list(psutil.process_iter())
        list(map(self._procs.append, map(ProcessMirror, _pcs, len(_pcs)*[self] )))
        # set cpu_percent sampler
        [ process_call_guard(p.cpu_percent) for p in self._procs ]
        # wait for samples to collect
        time.sleep(DEFAULT_INTERVAL)
        # collect the samples
        pcpu = [ process_call_guard(p.cpu_percent) for p in self._procs ]
        # and map them to the corresponding ProcessMirror object
        list(map(lambda a,b: a.set_pcpu(b), self._procs, pcpu))
        # fill mirrors dict for faster mirror searching
        self.mirrors = {}
        for p in self._procs: self.mirrors.setdefault(p.pid, p)

        self.bundles = []

        # create expendable copy of the process list)
        self._expendable = list(self._procs)

        # collect the group id's of process groups
        pgids = list(set([p._pgid for p in self._procs]))

        #kernelProcs = list(filter(lambda x: utils.is_kernel_thread(x), self._expendable))
        #list(map(self._expendable.remove, kernelProcs))

        mirrors_by_pgid = list(map(self.mirrors_by_pgid, pgids))
        mirrors_by_pgid.sort(key=lambda x: len(x), reverse=True)
        while len(self._expendable) > 0:
            for ms in mirrors_by_pgid:
                    self.bundles.append(ProcBundle(ms, pt=self))
                    self._clear_expendable()

        uniq_names = list(set(self.get_bundle_names()))
        for name in uniq_names:
            n = self._get_bundles_by_name(name)
            for b in n[1:]:
                n[0].merge(b)

        #    self.get_bundle_names()



    def _clear_expendable(self):
        list(map(lambda p: self._expendable.remove(p) if p in self.bundled() and p in
            self._expendable else None, self._expendable))


    def mirrors_by_pgid(self, pgid):
        return list(filter(lambda x: x._pgid == pgid,  self._procs))

    def mirror_by_pid(self, pid):
        if pid in self.mirrors.keys():
            return self.mirrors[pid]
        else:
            return None

    def bundled(self) -> list:
        ret = []
        for b in self.bundles:
            ret.extend(b.proclist)
        return ret

    def get_bundle_names(self) -> list:
        return [ b.bundle_name for b in self.bundles ]

    def _get_bundles_by_name(self, name):
        if name in self.get_bundle_names():
            return list(filter(lambda x: x.bundle_name == name, self.bundles))
        return None

    def get_bundle_by_name(self, name):
        if name in self.get_bundle_names():
            return list(filter(lambda x: x.bundle_name == name, self.bundles))[0]
        return None

    def get_idle(self, interval=DEFAULT_INTERVAL):
        return psutil.cpu_times_percent(interval=interval).idle
