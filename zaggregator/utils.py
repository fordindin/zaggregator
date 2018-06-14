#!/usr/bin/env python

from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, StringMatcher
import os, sys
import logging as log
import psutil
import json
import zaggregator

DEFAULT_FUZZY_THRESHOLD = 53
class ProcessGone(Exception): pass

def eprint(*args, **kwargs):
    """
        Wrapper around built-in `print' function which allow to print
        into sys.stderr instead of sys.stdout
    """
    print(*args, file=sys.stderr, **kwargs)

def reduce_sequence(seq:list) -> str:
    """
        Reduce sequence of names to single name
    """
    if len(seq) == 1: return seq[0]

    def single_pass(iseq):
        matches = []
        fuzzy_strings = iseq
        for i in range(len(fuzzy_strings)-1):
            a = fuzzy_strings[i]
            b = fuzzy_strings[i+1]
            sm = SequenceMatcher(a=a, b=b)
            match = sm.get_matching_blocks()[0]
            matches.append(a[match.a:match.size])
        return matches

    sp = single_pass(seq)

    while len(sp) > 1:
        sp = single_pass(sp)

    return sp[0].strip("[]:- ")

def fuzzy_match(a:str, b:str, threshold=DEFAULT_FUZZY_THRESHOLD) -> bool:
    """
        Checks if there a fussy match between two strings
    """
    score = fuzz.partial_ratio(a,b)
    log.debug("Fuzzy score: {} ({},{})".format(score, a, b))
    if score > threshold:
        return True
    else:
        return False

def fuzzy_sequence_match(seq:list) -> bool:
    """
        Checks if all strings in sequence are fuzzy match
    """
    for i in range(len(seq)-1):
        match = fuzzy_match(seq[i],seq[i+1])
        if not match:
            return False
    return True

def is_proc_group_parent(proc) -> bool:
    """
        Checks if process is a group parent
    """
    if os.uname().sysname == 'Darwin':
        fproc_names = filter(lambda x: len(x.cmdline()) > 0, proc.children())
        procs_names = [ p.cmdline()[0] for p in fproc_names ]
        procs_names.append(proc.cmdline()[0])
    else:
        procs_names = [ p.name() for p in proc.children() ]
        procs_names.append(proc.name())
    if len(procs_names) <= 1:
        return False
    if fuzzy_sequence_match(procs_names):
        return True
    #if len(proc.children()) > 2 and proc.parent():
    #    return True
    return False

def parent_has_single_child(proc) -> bool:
    """
        Checks if process's parent has only one child
    """
    if not proc or not proc.parent: return False
    try:
        parent = proc.parent()
        if not parent: return False
        return len(proc.parent().children()) == 1
    except psutil.NoSuchProcess:
        raise ProcessGone


def is_kernel_thread(proc) -> bool:
    """
        Checks if process is a kernel process/thread
    """
    if isinstance(proc, psutil.Process):
        if os.getpgid(proc.pid) == 0:
            return True
    elif isinstance(proc, zaggregator.ProcessMirror):
        if proc._pgid == 0:
            return True
    return False

def is_leaf_process(proc) -> bool:
    """
        Checks if process has no children
    """

    try:
        if len(proc.children()) == 0 and len(proc.parent().children()) == 1:
                return True
        return False
    except psutil.NoSuchProcess:
        raise ProcessGone

def is_proc_in_bundle(proc, bundle) -> bool:
    """
        Checks if process in ProcBundle
    """
    return (proc in bundle.proclist)

def is_proc_similar_to(proc1, proc2) -> bool:
    """
        Checks if two processes are similar
    """
    if fuzzy_match(proc1.cmdline(),proc2.cmdline(), threshold=90) \
            and proc1.cwd() == proc2.cwd():
                return True
    return False

def discovery_json(names):
    """
        Returns bundle names in Zabbix autodiscovery JSON format
    """
    template = { "data" : [ ]}
    for bn in names:
        template["data"].append({ "{#PROCGROUP}": bn, })
    template["data"].append({ "{#PROCGROUP}": 'idle', })
    return json.dumps(template)

