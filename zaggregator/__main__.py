#!/usr/bin/env python

import psutil
import sys
import logging
from fuzzywuzzy import fuzz
from zaggregator.procbundle import ProcTable
import json


if __name__ == '__main__':
    pt = ProcTable()

    if sys.argv[1] == 'discovery':
        template = { "data" : [ ]}
        for bn in pt.get_bundle_names():
            template["data"].append({ "{#PROCGROUP}": bn, })
        print(json.dumps(template))



