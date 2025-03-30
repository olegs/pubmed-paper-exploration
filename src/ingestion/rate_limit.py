# Credit: https://stackoverflow.com/a/64845203 and https://stackoverflow.com/a/43727014

import time
import threading


# make it work nice across threads
def RateLimited(max_per_second):
    """
    Decorator that make functions not be called faster than
    """
    lock = threading.Lock()
    minInterval = 1.0 / float(max_per_second)

    def decorate(func):
        lastTimeCalled = [0.0]

        def rateLimitedFunction(*args, **kwargs):
            lock.acquire()
            elapsed = time.process_time() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed

            if leftToWait > 0:
                time.sleep(leftToWait)

            lock.release()

            ret = func(*args, **kwargs)
            lastTimeCalled[0] = time.process_time()
            return ret

        return rateLimitedFunction

    return decorate


CALLS_PER_SECOND = 3


@RateLimited(CALLS_PER_SECOND)
def check_limit():
    """Empty function just to check for calls to API"""
    return
