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
        print(*args, file=sys.stderr, **kwargs)

def reduce_sequence(seq) -> list:
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

def fuzzy_match(a, b, threshold=DEFAULT_FUZZY_THRESHOLD) -> bool:
    score = fuzz.partial_ratio(a,b)
    log.debug("Fuzzy score: {} ({},{})".format(score, a, b))
    if score > threshold:
        return True
    else:
        return False

def fuzzy_sequence_match(seq) -> bool:
    for i in range(len(seq)-1):
        match = fuzzy_match(seq[i],seq[i+1])
        if not match:
            return False
    return True

def is_proc_group_parent(proc) -> bool:
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
    if not proc or not proc.parent: return False
    try:
        parent = proc.parent()
        if not parent: return False
        return len(proc.parent().children()) == 1
    except psutil.NoSuchProcess:
        raise ProcessGone


def is_kernel_thread(proc) -> bool:
    if isinstance(proc, psutil.Process):
        if os.getpgid(proc.pid) == 0:
            return True
    elif isinstance(proc, zaggregator.ProcessMirror):
        if proc._pgid == 0:
            return True
    return False

def is_leaf_process(proc) -> bool:
    try:
        if len(proc.children()) == 0 and len(proc.parent().children()) == 1:
                return True
        return False
    except psutil.NoSuchProcess:
        raise ProcessGone

def is_proc_in_bundle(proc, bundle) -> bool:
    return (proc in bundle.proclist)

def is_proc_similar_to(proc1, proc2) -> bool:
    if fuzzy_match(proc1.cmdline(),proc2.cmdline(), threshold=90) \
            and proc1.cwd() == proc2.cwd():
                return True
    return False

def discovery_json(names):
    template = { "data" : [ ]}
    for bn in names:
        template["data"].append({ "{#PROCGROUP}": bn, })
    template["data"].append({ "{#PROCGROUP}": 'idle', })
    return json.dumps(template)

