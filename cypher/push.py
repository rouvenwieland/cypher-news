"""Web Push (VAPID). Keys come from env: VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY (generate with `python -m cypher.vapid`)."""
import json, os


def public_key():
    return os.environ.get('VAPID_PUBLIC_KEY', '')


def send(sub_json, title, body, url='/'):
    """Returns True if sent, False if subscription is dead/unconfigured."""
    priv = os.environ.get('VAPID_PRIVATE_KEY')
    if not priv or not sub_json:
        return False
    from pywebpush import webpush, WebPushException
    try:
        webpush(subscription_info=json.loads(sub_json), data=json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=priv, vapid_claims={'sub': os.environ.get('VAPID_SUBJECT', 'mailto:admin@example.com')}, ttl=3600)
        return True
    except WebPushException:
        return False
    except Exception:
        return False
