import argparse
import sys
from zaggregator import sqlite
from zaggregator.utils import discovery_json, eprint

checks = [ "pcpu", "memrss", "memvms", "ctxvol", "ctxinvol" ]


def discover():
    """ Returns bundles list in Zabbix autodiscovery JSON format """
    print(discovery_json(sqlite.get_bundle_names()))

def check(opts):
    """ Returns value for specified bundle and check type """
    bname, check = opts
    if check not in checks:
        eprint(
            "\tInvalid check argument: \'{}\'\n\tSupported options are: \'{}\'".format(
            check, "','".join(checks)))
        sys.exit(1)
    print(sqlite.get(bname, check))

def main(*args, **kwargs):
    """ main module """
    parser = argparse.ArgumentParser(description='Zabbix aggregator client.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-discover', action='store_true',
        help="Discover and print out list of bundles in Zabbix autodiscovery JSON format.")
    group.add_argument('-bundle', nargs=2, metavar=("<bundleName>", "<check>"),
        help="Bundle name to check stats on. Check can be one of: pcpu, rss, vms, ctxvol, ctxinvol",)
    args = parser.parse_args()

    if args.discover:
        discover()
    if args.bundle:
        check(args.bundle)


if __name__ == '__main__':
    main()
