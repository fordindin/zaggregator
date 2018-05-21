#!/usr/bin/env python

from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, StringMatcher
import os
import logging as log

def reduce_sequence(seq):
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

    return sp[0]

def fuzzy_match(a,b):
    score = fuzz.partial_ratio(a,b)
    log.debug("Fuzzy score: {} ({},{})".format(score, a, b))
    if score > 53:
        return True
    else:
        return False

def fuzzy_sequence_match(seq):
    for i in range(len(seq)-1):
        match = fuzzy_match(seq[i],seq[i+1])
        if not match:
            return False
    return True

def is_proc_group_parent(proc):
    if os.uname().sysname == 'Darwin':
        procs_names = [ p.cmdline()[0] for p in proc.children() ]
        procs_names.append(proc.cmdline()[0])
    else:
        procs_names = [ p.name() for p in proc.children() ]
        procs_names.append(proc.name())
    if len(procs_names) <= 1:
        return False
    if fuzzy_sequence_match(procs_names):
        return True
    return False
