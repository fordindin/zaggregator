import asyncio
import sys, os
import zaggregator
import time
import setproctitle
from zaggregator import sqlite


if len(sys.argv) > 1:
    pidfile = sys.argv[1]
    with open(pidfile, "w") as fd:
        fd.write(str(os.getpid()))

delay = 30
loop = asyncio.get_event_loop()

def collect_data(bundle) -> (str, int, int, float):
    """  Collect data """
    return  (bundle.bundle_name, bundle.get_n_ctx_switches_vol(),
            bundle.get_memory_info_rss(),
            bundle.get_cpu_percent())

def zag_sampler_loop(lc):
    """ Main sampler loop """
    loop, callback = lc

    loop.call_later(delay, callback, lc)
    pt = zaggregator.ProcTable()
    for n in pt.get_bundle_names():
        b = pt.get_bundle_by_name(n)
        sqlite.add_record(
                (
                    b.bundle_name,
                    b.get_memory_info_rss(),
                    b.get_memory_info_vms(),
                    b.get_n_ctx_switches_vol(),
                    b.get_n_ctx_switches_invol(),
                    b.get_cpu_percent(),
                    ))

def start() -> None:
    """
        initialize and start main daemon loop
    """

    setproctitle.setproctitle('zaggregator')
    lc = (loop, callback)
    loop.call_later(delay, callback, lc)

    loop.run_forever()
    loop.close()

callback = zag_sampler_loop
