"""Local server for browser tests: fake OpenRouter + fake sources (no internet needed)."""
import os, sys, tempfile, threading
from http.server import HTTPServer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
d = tempfile.mkdtemp()
os.environ.update(DB_PATH=d + '/e2e.db', SECRET_KEY='e2e', MODEL_PRIMARY='test/primary:free', MODEL_VISION='test/vision:free', COOKIE_SECURE='0')
from tests.conftest import FakeOR
srv = HTTPServer(('127.0.0.1', 0), FakeOR); threading.Thread(target=srv.serve_forever, daemon=True).start()
from cypher import ai, sources
ai.BASE = f'http://127.0.0.1:{srv.server_port}'
item = {'platform': 'reddit', 'account': 'r/berlin', 'kind': 'post', 'text': 'Konzert im Mauerpark heute Abend', 'url': 'https://example.com/a', 'taken_at': '2026-10-06T10:00:00+00:00', 'image_url': ''}
sources.news = lambda t: [dict(item, platform='news', kind='news', account='Testblatt', text=f'{t}: Meldung', url='https://example.com/n')]
sources.FETCHERS['news'] = sources.news
sources.FETCHERS['reddit'] = lambda v: [item]
import app
app.SECURE = False
app.app.run(port=int(sys.argv[1]), debug=False)
