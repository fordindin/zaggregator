#!/usr/bin/env python

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Run unit tests. This is invoked by:

$ python -m psutil.tests
"""

import contextlib
import optparse
import os
import sys

from zaggregator.tests import run_suite


HERE = os.path.abspath(os.path.dirname(__file__))

def main():
    usage = "%s -m psutil.tests [opts]" % sys.argv[0]
    parser = optparse.OptionParser(usage=usage, description="run unit tests")
    parser.add_option("-i", "--install-deps",
                      action="store_true", default=False,
                      help="don't print status messages to stdout")

    opts, args = parser.parse_args()
    run_suite()

main()
