import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tests.calls import CALLS


class FakeOR(BaseHTTPRequestHandler):
    """Stands in for OpenRouter: returns a valid drop JSON for text prompts, a description for image prompts."""
    def log_message(self, *a): pass

    def do_GET(self):
        ok = self.headers.get('Authorization', '') == 'Bearer sk-or-good-key-0000000000000000'
        self.send_response(200 if ok else 401); self.end_headers(); self.wfile.write(b'{}')

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        CALLS.append((self.headers.get('Authorization'), body['model']))
        if 'sk-or-bad' in self.headers.get('Authorization', ''):
            self.send_response(401); self.end_headers(); return
        c = body['messages'][-1]['content']
        if isinstance(c, list):
            out = 'Konzertplakat: Sa 12.10., Berghain, Einlass 23 Uhr.'
        else:
            out = json.dumps({'title': 'Testdrop', 'intro': 'Hallo.', 'items': [{'idx': 0, 'category': 'Konzerte', 'title': 'Erster Treffer', 'summary': 'Zusammenfassung.', 'when': 'Heute'}]})
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps({'choices': [{'message': {'content': out}}]}).encode())


@pytest.fixture(scope='session')
def fake_or():
    s = HTTPServer(('127.0.0.1', 0), FakeOR)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{s.server_port}'
    s.shutdown()


@pytest.fixture()
def client(tmp_path, monkeypatch, fake_or):
    monkeypatch.setenv('DB_PATH', str(tmp_path / 't.db'))
    monkeypatch.setenv('SECRET_KEY', 'test-secret')
    monkeypatch.setenv('MODEL_PRIMARY', 'test/primary:free')
    monkeypatch.setenv('MODEL_VISION', 'test/vision:free')
    monkeypatch.setenv('COOKIE_SECURE', '0')
    monkeypatch.setenv('CRON_SECRET', 'cron')
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    import cypher.db, cypher.ai, cypher.scheduler, cypher.sources
    monkeypatch.setattr(cypher.db, 'DB_PATH', str(tmp_path / 't.db'))
    monkeypatch.setattr(cypher.ai, 'BASE', fake_or)
    CALLS.clear()
    import app as _a; _a._hits.clear()
    import app as appmod
    monkeypatch.setattr(appmod, 'SECURE', False)
    # offline: deterministic fake sources instead of the real internet
    item = {'platform': 'reddit', 'account': 'r/berlin', 'kind': 'post', 'text': 'Konzert im Mauerpark heute Abend', 'url': 'https://example.com/a', 'taken_at': '2026-10-06T10:00:00+00:00', 'image_url': ''}
    monkeypatch.setattr(cypher.sources, 'news', lambda t: [dict(item, platform='news', kind='news', account='Testblatt', text=f'{t}: Meldung', url='https://example.com/n-' + t.replace(' ', ''))])
    monkeypatch.setitem(cypher.sources.FETCHERS, 'reddit', lambda v: [item])
    monkeypatch.setitem(cypher.sources.FETCHERS, 'news', cypher.sources.news)
    c = appmod.app.test_client()
    return c
