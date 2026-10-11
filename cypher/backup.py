"""Free hosts have no persistent disk. This keeps the SQLite file safe in a PRIVATE Hugging Face dataset repo.
Enabled when HF_TOKEN and BACKUP_REPO (e.g. "yourname/cypher-news-data") are set. Restore at boot, upload every few minutes if changed."""
import hashlib, os, shutil, sqlite3, tempfile, threading, time

from . import db

FILE = 'cypher.db'
STATE = {'enabled': False, 'last_upload': None, 'last_error': '', 'restore': ''}  # shown on /healthz (never contains secrets)


def enabled():
    return bool(os.environ.get('HF_TOKEN') and os.environ.get('BACKUP_REPO'))


def _api():
    from huggingface_hub import HfApi
    return HfApi(token=os.environ['HF_TOKEN'])


def restore(download=None):
    """Restore the last backup if no local DB exists yet.
    Returns 'restored', 'fresh' (nothing to restore / DB already there) or 'error' (backup exists but could not be loaded).
    IMPORTANT: the downloaded file lives in the read-only HF cache, so it is copied WITHOUT its permission bits (copyfile)
    and made writable; a plain shutil.copy produced a read-only DB and every write failed ('attempt to write a readonly database')."""
    if not enabled() or os.path.exists(db.DB_PATH):
        STATE['restore'] = 'fresh'
        return 'fresh'
    try:
        if download is None:
            from huggingface_hub import hf_hub_download
            from huggingface_hub.utils import EntryNotFoundError, RepositoryNotFoundError
            try:
                src = hf_hub_download(os.environ['BACKUP_REPO'], FILE, repo_type='dataset', token=os.environ['HF_TOKEN'], force_download=True)
            except (EntryNotFoundError, RepositoryNotFoundError):
                STATE['restore'] = 'fresh'
                return 'fresh'  # first run: nothing saved yet
        else:
            src = download()
        os.makedirs(os.path.dirname(os.path.abspath(db.DB_PATH)), exist_ok=True)
        shutil.copyfile(src, db.DB_PATH)
        os.chmod(db.DB_PATH, 0o600)
        with db.conn() as c:  # must be a healthy, writable DB
            if c.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise RuntimeError('backup file is corrupt')
            c.execute("INSERT OR REPLACE INTO cache(k,ts,v) VALUES('restore_probe',0,'1')")
        STATE['restore'] = 'restored'
        return 'restored'
    except Exception as e:
        try:
            os.remove(db.DB_PATH)  # never keep a half-restored DB
        except OSError:
            pass
        STATE.update(restore='error', last_error=f'restore: {type(e).__name__}: {str(e)[:120]}')
        print('restore failed:', STATE['last_error'], flush=True)
        return 'error'


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
        STATE.update(last_upload=time.time(), last_error='')
        return h
    except Exception as e:
        STATE['last_error'] = f'{type(e).__name__}: {str(e)[:160]}'
        print('backup failed:', STATE['last_error'], flush=True)
        return last_hash


def restore_or_die(retries=(2, 5, 10, 20)):
    """Boot guard: if a backup exists but cannot be loaded, refuse to start (the host restarts us) instead of running with an
    empty DB that would later overwrite the good backup."""
    status = restore()
    for wait in retries:
        if status != 'error':
            return status
        time.sleep(wait)
        status = restore()
    if status == 'error':
        raise RuntimeError('backup exists but could not be restored; refusing to start with an empty database')
    return status


def start_thread(interval=300):
    STATE['enabled'] = True

    def loop():
        h = None
        while True:
            h = upload_if_changed(h)
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()
