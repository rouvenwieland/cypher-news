"""Web Push (VAPID). Keys come from env: VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY (generate with `python -m cypher.vapid`)."""
import json, os


def _generate():
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    k = ec.generate_private_key(ec.SECP256R1())
    b = lambda x: base64.urlsafe_b64encode(x).decode().rstrip('=')
    return {'private': b(k.private_numbers().private_value.to_bytes(32, 'big')),
            'public': b(k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))}


def keys():
    """VAPID keys from env, else generated once and kept in the DB (so push works without any setup)."""
    if os.environ.get('VAPID_PRIVATE_KEY') and os.environ.get('VAPID_PUBLIC_KEY'):
        return {'private': os.environ['VAPID_PRIVATE_KEY'], 'public': os.environ['VAPID_PUBLIC_KEY']}
    from . import db
    return db.setting('vapid', _generate)


def public_key():
    try:
        return keys()['public']
    except Exception:
        return ''


def send(sub_json, title, body, url='/'):
    """Returns True if sent, False if subscription is dead/unconfigured."""
    if not sub_json:
        return False
    priv = keys()['private']
    from pywebpush import webpush, WebPushException
    try:
        webpush(subscription_info=json.loads(sub_json), data=json.dumps({'title': title, 'body': body, 'url': url}),
                vapid_private_key=priv, vapid_claims={'sub': os.environ.get('VAPID_SUBJECT', 'mailto:admin@example.com')}, ttl=3600)
        return True
    except WebPushException:
        return False
    except Exception:
        return False
