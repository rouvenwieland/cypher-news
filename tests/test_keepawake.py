"""The keep-awake workflow must ping all day, no denser than every 10 minutes, and stay within GitHub's 6 h job limit."""
import pathlib, re

WF = (pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows' / 'daily-drop.yml').read_text(encoding='utf-8')


def _num(name):
    return int(re.search(rf'^\s+{name}:\s*(\d+)\s*(#.*)?$', WF, re.M).group(1))


def test_ping_interval_not_denser_than_ten_minutes():
    assert _num('PING_INTERVAL_S') >= 600
    assert 'sleep "$PING_INTERVAL_S"' in WF


def test_run_fits_github_job_limit():
    assert _num('timeout-minutes') <= 360
    assert _num('RUN_SECONDS') + 600 <= _num('timeout-minutes') * 60  # loop length plus one ping interval


def test_schedule_covers_the_whole_day():
    s = _starts()
    assert s, 'no cron entries'
    gaps = [(b - a) for a, b in zip(s, s[1:] + [s[0] + 1440])]
    assert max(gaps) * 60 <= _num('RUN_SECONDS')  # every start comes before the previous run ends, so queued runs chain without a gap


# --- verification round 2 (2026-10-14) ---------------------------------------------------------------------------------
def _expand(field, top):
    out = set()
    for part in field.split(','):
        rng, _, step = part.partition('/')
        lo, hi = (0, top - 1) if rng == '*' else (int(rng.split('-')[0]), int(rng.split('-')[-1]))
        out |= set(range(lo, hi + 1, int(step or 1)))
    return out


def _starts():
    """All cron start times of a day in minutes."""
    return sorted(h * 60 + m for mf, hf in re.findall(r"cron:\s*'(\S+) (\S+) \* \* \*'", WF)
                  for m in _expand(mf, 60) for h in _expand(hf, 24))


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


def test_timeout_also_covers_a_slow_last_ping():
    """The loop ends at most one sleep plus one ping AFTER RUN_SECONDS. A slow or failing last curl (Render waking up, outage)
    used to push the job past timeout-minutes: the run was killed and reported as failed."""
    m = re.search(r'-m (\d+) --retry (\d+) --retry-delay (\d+)', WF)
    worst_curl = int(m.group(1)) * (int(m.group(2)) + 1) + int(m.group(2)) * int(m.group(3))
    setup = 60
    assert _num('RUN_SECONDS') + _num('PING_INTERVAL_S') + worst_curl + setup <= _num('timeout-minutes') * 60 <= 360 * 60
