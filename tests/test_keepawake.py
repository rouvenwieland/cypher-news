"""The keep-awake workflow must ping all day, no denser than every 10 minutes, and stay within GitHub's 6 h job limit."""
import pathlib, re

WF = (pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows' / 'daily-drop.yml').read_text(encoding='utf-8')


def _num(name):
    return int(re.search(rf'^\s+{name}:\s*(\d+)\s*$', WF, re.M).group(1))


def test_ping_interval_not_denser_than_ten_minutes():
    assert _num('PING_INTERVAL_S') >= 600
    assert 'sleep "$PING_INTERVAL_S"' in WF


def test_run_fits_github_job_limit():
    assert _num('timeout-minutes') <= 360
    assert _num('RUN_SECONDS') + 600 <= _num('timeout-minutes') * 60  # loop length plus one ping interval


def test_schedule_covers_the_whole_day():
    hours = sorted({int(h) for h in re.findall(r"cron:\s*'\d+ (\d+) \* \* \*'", WF)})
    assert hours, 'no cron entries'
    gaps = [(b - a) for a, b in zip(hours, hours[1:] + [hours[0] + 24])]
    assert max(gaps) * 3600 <= _num('RUN_SECONDS')  # every start comes before the previous run ends, so queued runs chain without a gap
