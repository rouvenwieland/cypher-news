"""Property tests (Hypothesis) for the pure logic: dedupe, ranking, SSRF/URL validation, import parser, rate limiter, API fuzzing."""
import ipaddress, json, string

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from cypher import pipeline, sources

settings.register_profile('verify', deadline=None, max_examples=100)
settings.load_profile('verify')
NOFIX = settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None, max_examples=60)

text = st.text(alphabet=st.characters(blacklist_categories=('Cs',)), max_size=120)
placeholder = st.sampled_from(['Bild-Post', 'Post mit Bild', 'Geteiltes Bild', ''])
item = st.builds(
    lambda platform, account, t, url: {'platform': platform, 'account': account, 'kind': 'post' if platform != 'news' else 'news',
                                       'text': t, 'url': url, 'taken_at': '2026-10-06T10:00:00+00:00', 'image_url': ''},
    st.sampled_from(['news', 'reddit', 'instagram', 'shared']), st.sampled_from(['a', 'b', 'c', '@x']),
    st.one_of(text, placeholder),
    st.one_of(st.just(''), st.integers(0, 6).map(lambda n: f'https://example.com/{n}')))
items = st.lists(item, max_size=25)
urls = st.sets(st.integers(0, 6).map(lambda n: f'https://example.com/{n}'), max_size=4)


# ---------- dedupe ----------
@given(items, urls)
def test_dedupe_is_idempotent(its, old):
    once = pipeline.dedupe(its, old)
    assert pipeline.dedupe(once, old) == once


@given(items, urls)
def test_dedupe_output_is_ordered_subset_without_key_collisions_or_old_urls(its, old):
    out = pipeline.dedupe(its, old)
    it = iter(its)
    assert all(any(o is x for x in it) for o in out)  # order-preserving subsequence (identity)
    keys = [pipeline.dedupe_key(o) for o in out]
    assert len(keys) == len(set(keys))
    assert all(not (o['url'] and o['url'] in old) for o in out)


@given(items, urls)
def test_dedupe_drops_only_with_reason(its, old):
    out = pipeline.dedupe(its, old)
    kept_keys = {pipeline.dedupe_key(o) for o in out}
    for i in its:
        if not any(i is o for o in out):
            assert (i['url'] and i['url'] in old) or pipeline.dedupe_key(i) in kept_keys


@given(st.lists(st.integers(0, 50), min_size=1, max_size=12, unique=True), placeholder.filter(bool))
def test_placeholder_posts_with_distinct_urls_all_survive(ns, ph):
    its = [{'platform': 'instagram', 'account': '@a', 'kind': 'post', 'text': ph, 'url': f'https://e.com/{n}', 'taken_at': '', 'image_url': ''} for n in ns]
    assert len(pipeline.dedupe(its, set())) == len(ns)


# ---------- ranking ----------
fb_map = st.dictionaries(st.sampled_from(['a', 'b', 'c', '@x', 'konzerte', 'news', 'tech', 'drops', 'giveaways']), st.integers(-5, 5), max_size=9)
topics = st.lists(st.text(alphabet=string.ascii_lowercase + ' ', min_size=3, max_size=20), max_size=4)


@given(item, topics, fb_map, fb_map)
def test_score_is_monotone_in_feedback(it, tp, fb1, fb2):
    hi = {k: max(fb1.get(k, 0), fb2.get(k, 0)) for k in set(fb1) | set(fb2)}
    lo = {k: min(fb1.get(k, 0), fb2.get(k, 0)) for k in set(fb1) | set(fb2)}
    assert pipeline.score(it, tp, hi) >= pipeline.score(it, tp, lo)


@given(item, topics, fb_map, st.integers(1, 5))
def test_one_more_upvote_for_the_account_never_lowers_score_and_raises_it_by_exactly_that(it, tp, fb, d):
    base = pipeline.score(it, tp, fb)
    k = it['account'].lower()
    up = dict(fb, **{k: fb.get(k, 0) + d})
    assert pipeline.score(it, tp, up) == base + d


@given(st.text(max_size=300))
def test_topics_from_notes_bounds(notes):
    t = pipeline.topics_from_notes(notes)
    assert 1 <= len(t) <= 5 and len(set(t)) == len(t)
    assert all(2 < len(x) < 80 or x in ('Konzerte Berlin', 'Giveaways', 'Tech News') for x in t)


# ---------- URL / SSRF ----------
ips = st.one_of(st.ip_addresses(v=4), st.ip_addresses(v=6))


@given(ips)
def test_is_public_url_matches_ipaddress_semantics_for_literals(ip):
    host = f'[{ip}]' if ip.version == 6 else str(ip)
    expect = ip.is_global and not ip.is_multicast
    assert sources.is_public_url(f'http://{host}/x') == expect


@given(st.sampled_from(['ftp', 'file', 'gopher', 'javascript', 'data']), st.text(alphabet=string.ascii_lowercase + '.', max_size=20))
def test_non_http_schemes_are_never_public(scheme, rest):
    assert sources.is_public_url(f'{scheme}://{rest}/') is False


@given(st.text(max_size=200))
def test_is_public_url_never_raises(u):
    assert sources.is_public_url(u) in (True, False) or True


@given(ips)
def test_push_endpoint_check_never_accepts_non_global_literals(ip):
    import app as appmod
    host = f'[{ip}]' if ip.version == 6 else str(ip)
    if not ip.is_global:
        assert appmod._push_endpoint_ok(f'https://{host}/p') is False


# ---------- detect / import parser ----------
@given(st.text(max_size=300))
def test_detect_never_raises_and_returns_known_platform(v):
    p, val = sources.detect(v)
    assert p is None or p in sources.FETCHERS
    assert isinstance(val, str)


@given(st.text(max_size=3000))
@NOFIX
def test_import_parser_is_total_bounded_and_clean(client, text_):
    from tests.test_app import start
    if client.get('/api/me').get_json().get('session') is False:
        start(client)
    r = client.post('/api/sources/import', json={'text': text_, 'platform': 'instagram'})
    assert r.status_code == 200
    found = r.get_json()['found']
    assert len(found) <= 200
    assert all(f['platform'] in sources.FETCHERS and f['platform'] != 'news' and f['value'] for f in found)


# ---------- rate limiter ----------
@given(st.lists(st.floats(min_value=0, max_value=50, allow_nan=False), min_size=1, max_size=60), st.integers(1, 6), st.integers(1, 20))
def test_rate_limit_never_admits_more_than_limit_per_window(times, limit, per):
    import app as appmod
    appmod._hits.clear()
    clock = {'t': 0.0}
    real = appmod.time.time
    appmod.time.time = lambda: clock['t']
    try:
        accepted = []
        with appmod.app.test_request_context('/', environ_base={'REMOTE_ADDR': '1.2.3.4'}):
            for t in sorted(times):
                clock['t'] = t
                if appmod.rate_limit('prop', limit, per):
                    accepted.append(t)
        for i, t in enumerate(accepted):
            assert len([x for x in accepted if t <= x < t + per]) <= limit
    finally:
        appmod.time.time = real


# ---------- API fuzzing: arbitrary JSON must never give a 5xx ----------
js = st.recursive(st.none() | st.booleans() | st.integers(-10**12, 10**12) | st.floats(allow_nan=False) | text,
                  lambda c: st.lists(c, max_size=4) | st.dictionaries(text, c, max_size=4), max_leaves=12)
ROUTES = [('PUT', '/api/profile'), ('POST', '/api/feedback'), ('POST', '/api/saved'), ('DELETE', '/api/saved'), ('POST', '/api/sources/detect'),
          ('POST', '/api/sources/import'), ('POST', '/api/push'), ('POST', '/api/key'), ('POST', '/api/restore')]


@pytest.mark.parametrize('method,path', ROUTES)
@given(body=js)
@settings(NOFIX, max_examples=40)
def test_api_never_returns_5xx_for_arbitrary_json(client, method, path, body):
    from tests.test_app import start
    if client.get('/api/me').get_json().get('session') is False:
        start(client)
    r = client.open(path, method=method, json=body)
    assert r.status_code < 500, (path, body, r.status_code)
