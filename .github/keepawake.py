"""Keep-awake for the free Render service, only inside a daily time window (Europe/Berlin).

Render's free plan gives 750 instance hours per month for the WHOLE account, a service that never sleeps would use ~730 of them.
So the service is pinged (GET /healthz, which also makes the built-in scheduler build due drops) only from 05:50 to 23:50 Berlin
time; at night it falls asleep 15 minutes after the last ping. The window follows the Berlin clock, so summer/winter time needs
no change (the workflow itself runs in UTC). Users can only pick drop times from 06:00 to 23:00 Berlin time (see DEPLOY.md).

Used by .github/workflows/daily-drop.yml. Environment: APP_URL, PING_INTERVAL_S (600), RUN_SECONDS (20400). Standard library only.
Pure functions and injectable clock/sleep/ping, so tests/test_keepawake.py can simulate whole days.
"""
import math, os, subprocess, sys, time
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo('Europe/Berlin')
WINDOW_START = 5 * 60 + 50    # 05:50 Berlin: ten minutes before the first possible drop (06:00), the service wakes up and loads the backup
WINDOW_END = 23 * 60 + 50     # 23:50 Berlin (exclusive): the last drop starts at 23:00, the service sleeps ~15 minutes after the last ping
DEFAULT_URL = 'https://cypher-news.onrender.com'
CURL_TIMEOUT, CURL_RETRIES, CURL_RETRY_DELAY = 90, 2, 15   # per ping: curl -m 90 --retry 2 --retry-delay 15
WORST_PING_S = CURL_TIMEOUT * (CURL_RETRIES + 1) + CURL_RETRIES * CURL_RETRY_DELAY   # 300 s: a ping that keeps failing


def berlin_minute(ts):
    """Minute of the day (0..1439) on the Berlin wall clock at epoch second `ts`."""
    d = datetime.fromtimestamp(ts, BERLIN)
    return d.hour * 60 + d.minute


def in_window(ts):
    return WINDOW_START <= berlin_minute(ts) < WINDOW_END


def next_window_start(ts):
    """Epoch second of the next 05:50 Berlin time after `ts` (summer/winter time included: aware datetimes)."""
    day = datetime.fromtimestamp(ts, BERLIN).date()
    for add in (0, 1):
        start = datetime.combine(day + timedelta(days=add), dtime(WINDOW_START // 60, WINDOW_START % 60), tzinfo=BERLIN).timestamp()
        if start > ts:
            return start


def ping(url):
    """GET /healthz with curl (-m is a TOTAL limit, unlike a socket timeout). True if it answered."""
    cmd = ['curl', '-fsS', '-m', str(CURL_TIMEOUT), '--retry', str(CURL_RETRIES), '--retry-delay', str(CURL_RETRY_DELAY),
           '-o', os.devnull, url.rstrip('/') + '/healthz']
    try:
        return subprocess.run(cmd, timeout=WORST_PING_S + 5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run(url, run_seconds, interval, now=time.time, sleep=time.sleep, do_ping=ping):
    """Ping every `interval` seconds while the Berlin clock is inside the window; outside it sleep until the window opens.
    Returns after `run_seconds` (GitHub limits a job to 6 h; the next run of the chain takes over). Returns the ping count."""
    end, n = now() + run_seconds, 0
    while True:
        t = now()
        if t >= end:
            return n
        if in_window(t):
            if not do_ping(url):
                print(f'ping failed at {datetime.fromtimestamp(t, BERLIN):%H:%M} Berlin time', flush=True)
            n += 1
            sleep(max(0, min(interval, end - now())))
        else:
            sleep(max(0, min(math.ceil(next_window_start(t) - t) + 1, end - t)))   # +1 s: wake up inside the window, not just before it


def main():
    url = os.environ.get('APP_URL', DEFAULT_URL)
    interval, seconds = int(os.environ.get('PING_INTERVAL_S', '600')), int(os.environ.get('RUN_SECONDS', '20400'))
    t = time.time()
    print(f'start {datetime.fromtimestamp(t, BERLIN):%Y-%m-%d %H:%M} Berlin time, window {WINDOW_START // 60:02d}:{WINDOW_START % 60:02d}-'
          f'{WINDOW_END // 60:02d}:{WINDOW_END % 60:02d}, in window: {in_window(t)}', flush=True)
    n = run(url, seconds, interval)
    print(f'done after {n} pings', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
