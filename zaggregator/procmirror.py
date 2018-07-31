#!/usr/bin/env python

import psutil
import logging
import os

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
        except Exception as e:
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
