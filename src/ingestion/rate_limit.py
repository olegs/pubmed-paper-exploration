#Credit: https://stackoverflow.com/a/64845203

from ratelimit import limits, sleep_and_retry

# 3 calls per second
CALLS = 3
RATE_LIMIT = 1

@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def check_limit():
    ''' Empty function just to check for calls to API '''
    return
