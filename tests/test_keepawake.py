"""The keep-awake job: pings only inside the Berlin-time window (05:50-23:50), never denser than every 10 minutes, the chain of runs
has no gaps inside the window, and the free Render hours (750 per month for the whole account) are not used up.
Needs the time zone database (Linux: system tzdata, Windows: `pip install tzdata`); without it the module is skipped."""
import importlib.util, pathlib, re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
from hypothesis import given, settings, strategies as st

ROOT = pathlib.Path(__file__).resolve().parent.parent
WF = (ROOT / '.github' / 'workflows' / 'daily-drop.yml').read_text(encoding='utf-8')
try:
    BERLIN = ZoneInfo('Europe/Berlin')
except ZoneInfoNotFoundError:
    pytest.skip('no time zone database (pip install tzdata)', allow_module_level=True)
_spec = importlib.util.spec_from_file_location('keepawake', ROOT / '.github' / 'keepawake.py')
K = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)

IDLE_S = 15 * 60  # Render's free service falls asleep after 15 minutes without a request


def _num(name):
    return int(re.search(rf'^\s+{name}:\s*(\d+)\s*(#.*)?$', WF, re.M).group(1))


def berlin(y, mo, d, h=0, mi=0, s=0):
    return datetime(y, mo, d, h, mi, s, tzinfo=BERLIN).timestamp()


def test_ping_interval_not_denser_than_ten_minutes():
    assert _num('PING_INTERVAL_S') >= 600


def test_workflow_runs_the_script():
    assert 'python3 .github/keepawake.py' in WF and 'actions/checkout@' in WF


def test_run_fits_github_job_limit():
    assert _num('timeout-minutes') <= 360
    # loop + a last ping that keeps failing (3 tries) + checkout/start
    assert _num('RUN_SECONDS') + K.WORST_PING_S + 60 <= _num('timeout-minutes') * 60


def test_worst_ping_matches_curl_flags():
    assert K.WORST_PING_S == K.CURL_TIMEOUT * (K.CURL_RETRIES + 1) + K.CURL_RETRIES * K.CURL_RETRY_DELAY


# --- the schedule of run starts (unchanged chain: one run starts every 2 h, queued runs follow each other without a gap) --------
def _expand(field, top):
    out = set()
    for part in field.split(','):
        rng, _, step = part.partition('/')
        lo, hi = (0, top - 1) if rng == '*' else (int(rng.split('-')[0]), int(rng.split('-')[-1]))
        out |= set(range(lo, hi + 1, int(step or 1)))
    return out


def _starts():
    """All cron start times of a day in minutes (UTC)."""
    return sorted(h * 60 + m for mf, hf in re.findall(r"cron:\s*'(\S+) (\S+) \* \* \*'", WF)
                  for m in _expand(mf, 60) for h in _expand(hf, 24))


def test_schedule_covers_the_whole_day():
    s = _starts()
    assert s, 'no cron entries'
    gaps = [(b - a) for a, b in zip(s, s[1:] + [s[0] + 1440])]
    assert max(gaps) * 60 <= _num('RUN_SECONDS')  # every start comes before the previous run ends, so queued runs chain without a gap


def test_one_dropped_or_late_start_leaves_no_gap():
    """GitHub may drop scheduled runs at busy times ("some queued jobs may be dropped"). One missing start must still leave
    a queued successor before the running chain ends, otherwise the free service falls asleep and drops come late."""
    s = _starts()
    for skip in range(len(s)):
        rest = s[:skip] + s[skip + 1:]
        gaps = [(b - a) for a, b in zip(rest, rest[1:] + [rest[0] + 1440])]
        assert max(gaps) * 60 <= _num('RUN_SECONDS'), f'without the start at {s[skip] // 60}:{s[skip] % 60:02d} there is a gap'


def test_no_start_at_the_top_of_the_hour():
    """GitHub: 'High load times include the start of every hour' (delays, dropped runs)."""
    assert all(m % 60 >= 10 for m in _starts())


# --- the window ---------------------------------------------------------------------------------------------------------------
def test_window_edges_on_a_normal_day_and_on_both_time_changes():
    for y, mo, d in ((2026, 7, 15), (2026, 12, 15), (2026, 10, 25), (2027, 3, 28)):   # summer, winter, end and start of summer time
        assert not K.in_window(berlin(y, mo, d, 5, 49, 59))
        assert K.in_window(berlin(y, mo, d, 5, 50))
        assert K.in_window(berlin(y, mo, d, 23, 49, 59))
        assert not K.in_window(berlin(y, mo, d, 23, 50))
        assert not K.in_window(berlin(y, mo, d, 3, 30)) and not K.in_window(berlin(y, mo, d, 0, 5))
        assert K.in_window(berlin(y, mo, d, 12))


def test_window_is_the_same_wall_clock_in_summer_and_winter():
    """UTC would shift by an hour: 05:50 CEST is 03:50 UTC, 05:50 CET is 04:50 UTC. The window must follow the Berlin clock."""
    assert datetime.fromtimestamp(berlin(2026, 7, 15, 5, 50), timezone.utc).hour == 3
    assert datetime.fromtimestamp(berlin(2026, 12, 15, 5, 50), timezone.utc).hour == 4
    assert K.in_window(berlin(2026, 7, 15, 5, 50)) and K.in_window(berlin(2026, 12, 15, 5, 50))
    assert not K.in_window(berlin(2026, 7, 15, 5, 50) - 1) and not K.in_window(berlin(2026, 12, 15, 5, 50) - 1)


def test_window_allows_every_selectable_drop_hour_with_a_build_reserve():
    """The app offers drops from DROP_FROM_MIN to DROP_TO_MIN (Berlin time, static/js/app.js). The service must be awake ten
    minutes before the first one and for at least half an hour after the last one (build time, retries)."""
    js = (ROOT / 'static' / 'js' / 'app.js').read_text(encoding='utf-8')
    lo, hi = (int(x) * 60 for x in re.search(r'DROP_FROM_MIN = (\d+) \* 60, DROP_TO_MIN = (\d+) \* 60', js).groups())
    assert K.WINDOW_START <= lo - 10
    assert K.WINDOW_END >= hi + 30
    for minute in range(lo, hi + 1, 60):
        assert K.WINDOW_START <= minute < K.WINDOW_END


def test_deploy_md_names_the_window_and_the_drop_hours():
    text = (ROOT / 'DEPLOY.md').read_text(encoding='utf-8')
    for needle in ('05:50', '23:50', '06:00', '23:00', '750'):
        assert needle in text, needle


@given(st.integers(min_value=int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()), max_value=int(datetime(2029, 1, 1, tzinfo=timezone.utc).timestamp())))
def test_next_window_start_is_0550_berlin_and_inside_the_window(ts):
    nxt = K.next_window_start(ts)
    d = datetime.fromtimestamp(nxt, BERLIN)
    assert nxt > ts and (d.hour, d.minute, d.second) == (5, 50, 0)
    assert nxt - ts <= 24 * 3600 + 3600   # never more than a day and a time change away
    assert K.in_window(nxt)


# --- simulation: runs back to back over several days, with a fake clock -----------------------------------------------------------
class Sim:
    """A fake clock. sleep() advances it, a ping takes `ping_s` seconds and is recorded."""
    def __init__(self, t0, ping_s=2):
        self.t, self.pings, self.ping_s = t0, [], ping_s

    def now(self): return self.t

    def sleep(self, s): self.t += s

    def ping(self, url):
        self.pings.append(self.t); self.t += self.ping_s
        return True


def simulate(t0, days, run_seconds=20400, interval=600, start_delay=30):
    """Chain of runs: each starts `start_delay` seconds (checkout, queue) after the previous one ended."""
    sim, stop = Sim(t0), t0 + days * 86400
    while sim.t < stop:
        K.run('x', run_seconds, interval, sim.now, sim.sleep, sim.ping)
        sim.t += start_delay
    return sim.pings


def _awake_seconds(pings, lo, hi):
    """Seconds between lo and hi in which the service is up: every ping keeps it up for 15 more minutes."""
    total, cover = 0, lo
    for p in pings:
        a, b = max(p, cover), min(p + IDLE_S, hi)
        if b > a:
            total += b - a
        cover = max(cover, p + IDLE_S)
    return total


@pytest.mark.parametrize('first_day', [(2026, 10, 22), (2027, 3, 26), (2026, 7, 1), (2026, 12, 20)])   # across both time changes and plain weeks
def test_chain_pings_only_inside_the_window_and_without_gaps(first_day):
    t0 = berlin(*first_day, 0, 7)
    pings = simulate(t0, 6)
    assert pings and all(K.in_window(p) for p in pings), 'a ping outside 05:50-23:50 Berlin time'
    by_day = {}
    for p in pings:
        by_day.setdefault(datetime.fromtimestamp(p, BERLIN).date(), []).append(p)
    days = sorted(by_day)[1:-1]            # full days only
    assert len(days) >= 4
    for day in days:
        ps = by_day[day]
        first = datetime.fromtimestamp(ps[0], BERLIN)
        assert (first.hour, first.minute) == (5, 50), f'{day}: first ping at {first:%H:%M:%S}'
        assert max(b - a for a, b in zip(ps, ps[1:])) <= 600 + 60, f'{day}: service could fall asleep inside the window'
        last = datetime.fromtimestamp(ps[-1], BERLIN)
        assert K.WINDOW_END * 60 - (last.hour * 3600 + last.minute * 60 + last.second) <= 660, f'{day}: last ping {last:%H:%M}'


@pytest.mark.parametrize('first_day', [(2026, 10, 22), (2027, 3, 26), (2026, 7, 1)])
def test_render_hours_per_day_stay_under_budget(first_day):
    """Awake time per Berlin day <= 18.5 h (window 18 h + 15 min idle after the last ping + a few minutes), also on the days with a
    time change. 31 days x 18.5 h = 574.5 h, which leaves more than 175 of the 750 monthly free hours to the other service."""
    t0 = berlin(*first_day, 0, 7)
    pings = simulate(t0, 6)
    for k in range(1, 5):
        day = datetime.fromtimestamp(t0, BERLIN).date() + timedelta(days=k)
        lo = datetime.combine(day, datetime.min.time(), tzinfo=BERLIN).timestamp()
        hi = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=BERLIN).timestamp()
        h = _awake_seconds(pings, lo, hi) / 3600
        assert 17.5 <= h <= 18.5, f'{day}: {h:.2f} h awake'
    assert 31 * 18.5 <= 750 - 175


def test_every_drop_hour_of_the_window_has_a_ping_within_a_few_minutes():
    """A drop at hh:00 is picked up by the first /healthz kick after hh:00: no more than one ping interval later."""
    t0 = berlin(2026, 10, 25, 0, 7)   # the day summer time ends
    pings = simulate(t0, 2)
    for h in range(6, 24):
        due = berlin(2026, 10, 25, h)
        nxt = min(p for p in pings if p >= due)
        assert nxt - due <= 660, f'{h}:00 -> next ping {(nxt - due) / 60:.1f} min later'


@settings(max_examples=60, deadline=None)
@given(st.integers(min_value=int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()), max_value=int(datetime(2028, 12, 1, tzinfo=timezone.utc).timestamp())),
       st.integers(min_value=60, max_value=20400), st.sampled_from([600, 900]))
def test_run_never_pings_outside_the_window_nor_beyond_its_length(t0, seconds, interval):
    sim = Sim(t0)
    K.run('x', seconds, interval, sim.now, sim.sleep, sim.ping)
    assert all(K.in_window(p) for p in sim.pings)
    assert sim.t - t0 <= seconds + sim.ping_s            # ends on time (a ping started just before the end may finish after it)
    assert len(sim.pings) <= seconds // interval + 1
    assert all(b - a >= interval for a, b in zip(sim.pings, sim.pings[1:]))   # never denser than the interval
