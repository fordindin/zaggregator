import asyncio
import sys

delay = 1

def zag_sampler_loop(lc):
    loop, callback = lc

    loop.call_later(delay, callback, lc)
    sys.stdout.write(".")
    sys.stdout.flush()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    callback = zag_sampler_loop
    lc = (loop, callback)
    loop.call_later(delay, callback, lc)

    loop.run_forever()
    loop.close()
