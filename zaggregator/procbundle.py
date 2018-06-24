#!/usr/bin/env python

import psutil
import logging
import os
import time
import zaggregator.utils as utils

DEFAULT_INTERVAL  = 1.0
interpreters = "python", "perl", "bash", "tcsh", "zsh",

class ProcessMirror:
    """
        Class provides cachable and transparent copy of psutil.Process
        with some fields overwritten to avoid direct calling of
        psutil.Process methods, as they are inconsistent for dead processes

    """
    def __init__(self, proc: psutil.Process, proctable):
        """
            Class constructor
        """

        _dead = False
        self._children = list()
        self._parent = 0
        parent = None

        self._proc, self._pt = proc, proctable
        try:
            self._pgid = os.getpgid(proc.pid)
        except:
            self._pgid = 0
            _dead = True

        if not _dead:
            parent = proc.parent()

        if parent:
            self._parent = parent.pid

        if not _dead:
            self._children = [ p.pid for p in proc.children() ]

        with proc.oneshot():
            if proc.is_running():
                self.rss = proc.memory_info().rss
                self.vms = proc.memory_info().vms
                self.ctx_vol = proc.num_ctx_switches().voluntary
                self.ctx_invol = proc.num_ctx_switches().involuntary
                self._cmdline = proc.cmdline()
                self.pcpu = None
                #self.pcpu += proc.cpu_percent(interval=DEFAULT_INTERVAL)
            else:
                self.rss = 0
                self.vms = 0
                self.ctx_vol = 0
                self.ctx_invol = 0
                self.cmdline = [ ]
                self.pcpu = 0.0

    def __str__(self):
        return "<{} name={} pid={} _pgid={} alive={} >\n".format(self.__class__.__name__,
                self.name(), self.pid,
                self._pgid, self.alive)

    def __repr__(self):
        return self.__str__()

    def __getattribute__(self, name: str):
        """
            Masquerade psutil.Process's fields and methods
        """
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
        """
            CPU percent values cannot be cached, so we need this
            trick to set it for all ProcessMirrors in one pass
        """
        self.pcpu = value

class EmptyBundle(Exception): pass

class ProcBundle:
    """
        Class represents bundle or group of processes associated
        by there process group ID and child-parent relations
    """
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
            children_pids = [ p.pid for p in lp._proc.children(recursive=True) ]
            for p in children_pids:
                mirror = self.proctable.mirror_by_pid(p)
                if mirror not in self.proctable.bundled():
                    self.append(mirror)

        try:
            self.bundle_name = self._name_from_self_proclist()
        except:
            self.bundle_name = None

        if not self.bundle_name:
            self.bundle_name = self.name_from_cmdargs(self.leader)

    def append(self, proc: ProcessMirror):
        """
            Append ProcessMirror to curent ProcBundle's processes list
        """
        self.proclist.append(proc)

    def merge(self, bundle):
        """
            Merge ProcBundle with current one
        """
        self.proclist.extend(bundle.proclist)
        self.proctable.bundles.remove(bundle)

    def _name_from_self_proclist(self) -> str:
        """
            Generate bundle name from aquired proclist
        """
        out = ""
        out = list(map(lambda x: x._cmdline, self.proclist ))
        filter_titles = lambda x: len(x) > 1 and len(list(filter(lambda x: x == '', x))) > 0
        # filter out all processes except proctitles
        proctitles = [ x[0] for x in list(filter(filter_titles, out)) ]
        out = utils.reduce_sequence(list(filter(lambda x: not x.startswith("sshd"),
            proctitles)))
        return out

    @staticmethod
    def name_from_cmdargs(proc: ProcessMirror):
        """
            Choses name for the ProcBundle from ProcessMirror's
            command line arguments
        """
        _cmdline = proc._cmdline
        if utils.is_kernel_thread(proc): return "kernel"
        # special case for processes with set-up titles
        # due some specific behaviour of /proc they are have
        # empty strings in their cmdargs, for example:
        # [ 'zaggregator', '', '', '', '' ]
        # using this behaviour we are identifying such processes
        # and returning proctitle itself
        if len(_cmdline) > 1 and len(list(filter(lambda x: x == '', _cmdline))) > 0:
            return _cmdline[0]
        cline = list(filter(lambda x: not x.startswith("-"), _cmdline))

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
            out = out.split()[0].strip(":")[:20]
        except IndexError:
            out = os.path.basename(_cmdline[0])

        return out

    def get_n_ctx_switches_vol(self) -> int:
        """
            Returns sum of voluntary context switches for all processes
            in the current bundle
        """
        return sum([p.ctx_vol for p in  self.proclist])

    def get_n_ctx_switches_invol(self) -> int:
        """
            Returns sum of involuntary context switches for all processes
            in the current bundle
        """
        return sum([p.ctx_invol for p in  self.proclist])

    def get_memory_info_rss(self) -> int:
        """
            Returns sum of resident memory sizes for all processes
            in the current bundle
        """
        return sum([p.rss for p in  self.proclist])

    def get_memory_info_vms(self) -> int:
        """
            Returns sum of virtual memory sizes for all processes
            in the current bundle
        """
        return sum([p.vms for p in  self.proclist])

    def get_cpu_percent(self) -> float:
        """
            Returns sum of consumed CPU percent for all processes
            in the current bundle
        """
        return sum([p.pcpu for p in  self.proclist])


def alive_or_false(proc):
    """ Singleton to filter-out dead processes """
    if proc.is_running():
        return proc
    return False

def process_call_guard(func, *args, **kwargs):
    """ Singleton to handle situation when process died
        after registering, but before sampling """

    try:
        return func(*args, **kwargs)
    except psutil.NoSuchProcess:
        return False

class ProcTable:
    """
        Class represents cached process table for the sampling period
    """
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
        """ Clean up expendable processes list from bundled processes """
        list(map(lambda p: self._expendable.remove(p) if p in self.bundled() and p in
            self._expendable else None, self._expendable))


    def mirrors_by_pgid(self, pgid: int) -> [ProcessMirror]:
        """ Returns ProcessMirrors by Process Group ID (pgid) """
        return list(filter(lambda x: x._pgid == pgid,  self._procs))

    def mirror_by_pid(self, pid: int) -> ProcessMirror:
        """ Returns ProcessMirrors by process pid """
        if pid in self.mirrors.keys():
            return self.mirrors[pid]
        else:
            return None

    def bundled(self) -> list:
        """
            Returns list of all ProcessMirrors in all registered ProcBundles
        """
        ret = []
        for b in self.bundles:
            ret.extend(b.proclist)
        return ret

    def get_bundle_names(self) -> list:
        """
            Returns list of names of registered ProcBundles
        """
        return [ b.bundle_name for b in self.bundles ]

    def _get_bundles_by_name(self, name: str):
        """
            Returns list of all registered bundles with the same name. In the
            normal state there shouldn't be any duplicates in the regisered
            Procbundle, so we need to get all the names to merge ProcBundles
            with similar names. Should't be called outside of ProcTable internal
            context.
        """
        if name in self.get_bundle_names():
            return list(filter(lambda x: x.bundle_name == name, self.bundles))
        return None

    def get_bundle_by_name(self, name: str):
        """
            Returns ProcBundle with desired name or None for non-existing bundles
        """
        if name in self.get_bundle_names():
            return list(filter(lambda x: x.bundle_name == name, self.bundles))[0]
        return None

    def get_idle(self, interval=DEFAULT_INTERVAL):
        """
            TODO: refactor this
        """
        return psutil.cpu_times_percent(interval=interval).idle
