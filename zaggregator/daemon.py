import asyncio
import sys
import zaggregator
import time
from zaggregator import sqlite

delay = 5
loop = asyncio.get_event_loop()

def collect_data(bundle) -> (str, int, int, float):
    return  (bundle.bundle_name, bundle.get_n_ctx_switches_vol(),
            bundle.get_memory_info_rss(),
            bundle.get_cpu_percent())

def zag_sampler_loop(lc):
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

    """
    map(lambda x: x.set_cpu_percent(), pt.get_bundle_names())
    # we chouldn't use asyncio.sleep here, because
    # this call should be mandatory syncronous
    # it separates first call of the bundle.set_cpu_percent
    # from the second one
    time.sleep(zaggregator.procbundle.DEFAULT_INTERVAL)
    print(list(map(collect_data, pt.bundles)))
    """

def start() -> None:
    """
        initialize and start main daemon loop
    """

    lc = (loop, callback)
    loop.call_later(delay, callback, lc)

    loop.run_forever()
    loop.close()

callback = zag_sampler_loop
