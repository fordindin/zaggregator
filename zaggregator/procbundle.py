#!/usr/bin/env python

import psutil
import logging
import os
import zaggregator.utils as utils
from zaggregator.procmirror import ProcessMirror
from zaggregator.config import metrics, interpreters


class EmptyBundle(Exception): pass
class BadProcess(Exception): pass

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
            iproc = proc

            while proc and not utils.is_kernel_thread(proc):
                proc = proc.parent()

            if not proc:
                return iproc

            return proc

        def go_bottom(proc):
            if not proc:
                return None
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

        self._set_bundle_name()
        """
        try:
            self.bundle_name = self._name_from_self_proclist()
        except:
            self.bundle_name = None

        if not self.bundle_name:
            self.bundle_name = self.name_from_cmdargs(self.leader)
        """

        self.ctx_vol = self.get_n_ctx_switches_vol()
        self.ctx_invol = self.get_n_ctx_switches_invol()
        self.vms = self.get_memory_info_vms()
        self.rss = self.get_memory_info_rss()
        self.pcpu = self.get_cpu_percent()
        """
        """

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

    def _set_bundle_name(self):
        """
            Set name for a bundle
            - handle special cases for {cron, sshd, getty, etc. }
            - check if leader has cmdargs or proctitle, and set
              the bundle name with according method
        """

        # special cases

        self.bundle_name = ProcBundle.name_from_cmdargs(self.leader)


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
        _candidate = None

        _cmdline = proc._cmdline
        if utils.is_kernel_thread(proc): return "kernel"
        # special case for processes with set-up titles
        # due some specific behaviour of /proc they are have
        # empty strings in their cmdargs, for example:
        # [ 'zaggregator', '', '', '', '' ]
        # using this behaviour we are identifying such processes
        # and returning proctitle itself
        if len(_cmdline) > 1 and len(list(filter(lambda x: x == '', _cmdline))) > 0:
            if _cmdline[0].find(" ") < 0:
                _candidate =  _cmdline[0]
            else:
                _candidate =  _cmdline[0].split()[0]

            return _candidate.strip(":-")

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

    def _get_attr(self, attr:str) -> int:
        """
            Returns summary for the attribute attr
        """
        filtered = filter(lambda x: x != None and getattr(x, attr) != None, self.proclist)
        return sum([getattr(p, attr) for p in  filtered])

    def get_n_ctx_switches_vol(self) -> int:
        """
            Returns sum of voluntary context switches for all processes
            in the current bundle
        """
        return self._get_attr("ctx_vol")


    def get_n_ctx_switches_invol(self) -> int:
        """
            Returns sum of involuntary context switches for all processes
            in the current bundle
        """
        return self._get_attr("ctx_invol")


    def get_memory_info_rss(self) -> int:
        """
            Returns sum of resident memory sizes for all processes
            in the current bundle
        """
        return self._get_attr("rss")


    def get_memory_info_vms(self) -> int:
        """
            Returns sum of virtual memory sizes for all processes
            in the current bundle
        """
        return self._get_attr("vms")


    def get_cpu_percent(self) -> float:
        """
            Returns sum of consumed CPU percent for all processes
            in the current bundle
        """
        return self._get_attr("pcpu")


'''
def alive_or_false(proc):
    """ Singleton to filter-out dead processes """
    if proc.is_running():
        return proc
    return False
'''
