"""Free hosts have no persistent disk. This keeps the SQLite file safe in a PRIVATE Hugging Face dataset repo.
Enabled when HF_TOKEN and BACKUP_REPO (e.g. "yourname/cypher-news-data") are set. Restore at boot, upload every few minutes if changed."""
import hashlib, os, shutil, sqlite3, tempfile, threading, time

from . import db

FILE = 'cypher.db'


def enabled():
    return bool(os.environ.get('HF_TOKEN') and os.environ.get('BACKUP_REPO'))


def _api():
    from huggingface_hub import HfApi
    return HfApi(token=os.environ['HF_TOKEN'])


def restore(download=None):
    """Download the last backup if the local DB does not exist yet. Returns True if restored."""
    if not enabled() or os.path.exists(db.DB_PATH):
        return False
    try:
        if download is None:
            from huggingface_hub import hf_hub_download
            download = lambda: hf_hub_download(os.environ['BACKUP_REPO'], FILE, repo_type='dataset', token=os.environ['HF_TOKEN'])
        src = download()
        os.makedirs(os.path.dirname(os.path.abspath(db.DB_PATH)), exist_ok=True)
        shutil.copy(src, db.DB_PATH)
        return True
    except Exception:
        return False


def snapshot():
    """Consistent copy of the live DB (SQLite online backup API)."""
    tmp = os.path.join(tempfile.mkdtemp(), FILE)
    with db.conn() as c:
        dst = sqlite3.connect(tmp)
        c.backup(dst); dst.close()
    return tmp


def upload_if_changed(last_hash, upload=None):
    """Returns the new hash. Raises nothing."""
    try:
        snap = snapshot()
        h = hashlib.sha256(open(snap, 'rb').read()).hexdigest()
        if h == last_hash:
            return h
        if upload is None:
            api = _api()
            api.create_repo(os.environ['BACKUP_REPO'], repo_type='dataset', private=True, exist_ok=True)
            upload = lambda p: api.upload_file(path_or_fileobj=p, path_in_repo=FILE, repo_id=os.environ['BACKUP_REPO'], repo_type='dataset')
        upload(snap)
        return h
    except Exception:
        return last_hash


def start_thread(interval=300):
    def loop():
        h = None
        while True:
            time.sleep(interval)
            h = upload_if_changed(h)
    threading.Thread(target=loop, daemon=True).start()
