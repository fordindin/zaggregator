#!/usr/bin/env python

import psutil
import sys
import logging
from fuzzywuzzy import fuzz
from zaggregator.procbundle import ProcTable, EmptyBundle
import json


if __name__ == '__main__':

    if len(sys.argv) > 0:
        try:
            pt = ProcTable()
        except EmptyBundle:
            print("0.0")
            sys.exit(0)
        if sys.argv[1] == 'discovery':
            template = { "data" : [ ]}
            for bn in pt.get_bundle_names():
                template["data"].append({ "{#PROCGROUP}": bn, })
            print(json.dumps(template))
        else:
            if sys.argv[1] in pt.get_bundle_names():
                bundle = pt.get_bundle_by_name(sys.argv[1])
                if not bundle:
                    print("0.0")
                    sys.exit(0)
                metrics = sys.argv[2]
                if metrics == "nconn":
                    print(bundle.get_n_connections())
                if metrics == "nfd":
                    print(bundle.get_n_fds())
                if metrics == "nfile":
                    print(bundle.get_n_open_files())
                if metrics == "ctxswvol":
                    print(bundle.get_n_ctx_switches_vol())
                if metrics == "ctxswinvol":
                    print(bundle.get_n_ctx_switches_invol())
                if metrics == "memrss":
                    print(bundle.get_memory_info_rss())
                if metrics == "pcpu":
                    print(bundle.get_cpu_percent())
            else:
                print("0.0")
                sys.exit(0)
