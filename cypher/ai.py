"""OpenRouter client. Model names ALWAYS come from the environment (MODEL_PRIMARY, MODEL_FALLBACK, MODEL_VISION)."""
import json, os, re
import requests

BASE = os.environ.get('OPENROUTER_BASE', 'https://openrouter.ai/api/v1')


class AIError(Exception):
    pass


def text_models():
    return [m for m in (os.environ.get('MODEL_PRIMARY'), os.environ.get('MODEL_FALLBACK')) if m]


def vision_models():
    return [m for m in (os.environ.get('MODEL_VISION'),) if m]


def chat(key, model, messages, max_tokens=2500, timeout=75):
    r = requests.post(f'{BASE}/chat/completions', timeout=timeout,
                      headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
                               'HTTP-Referer': 'https://github.com/rouvenwieland/cypher-news', 'X-Title': 'Cypher News'},
                      json={'model': model, 'messages': messages, 'max_tokens': max_tokens, 'temperature': 0.4, 'reasoning': {'enabled': False}})
    if r.status_code in (401, 403):
        raise AIError('key_invalid')
    if r.status_code == 402:
        raise AIError('no_credit')
    if r.status_code == 429:
        raise AIError('rate_limited')
    r.raise_for_status()
    try:
        t = (r.json()['choices'][0]['message']['content'] or '').strip()
    except Exception:
        t = ''
    if not t:
        raise AIError('empty')
    return t


def chat_chain(key, models, messages, **kw):
    """Try models in order; hard key errors abort immediately."""
    last = None
    for m in models:
        try:
            return chat(key, m, messages, **kw), m
        except AIError as e:
            if str(e) in ('key_invalid', 'no_credit'):
                raise
            last = e
        except Exception as e:  # network, 404 (model gone), 5xx
            last = e
    raise AIError(f'all_models_failed: {last}')


def extract_json(t):
    m = re.search(r'\{[\s\S]*\}', t)
    if not m:
        raise ValueError('no json')
    return json.loads(m.group(0))


def describe_image(key, b64):
    ask = ('Beschreibe in 1-2 Saetzen auf Deutsch, was auf dem Bild zu sehen ist. Lies sichtbaren Text vor. '
           'Nenne Event-Infos (Datum, Ort, Anlass) und Giveaway-/Drop-/Preis-Hinweise, falls erkennbar. Keine Personen identifizieren.')
    msg = [{'role': 'user', 'content': [{'type': 'text', 'text': ask},
                                         {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + b64}}]}]
    try:
        t, m = chat_chain(key, vision_models(), msg, max_tokens=300, timeout=45)
        return t[:400], m
    except AIError as e:
        if str(e) in ('key_invalid', 'no_credit'):
            raise
        return '', ''
    except Exception:
        return '', ''


def check_key(key):
    """Cheap validity check against OpenRouter's key endpoint."""
    try:
        r = requests.get(f'{BASE}/auth/key', headers={'Authorization': f'Bearer {key}'}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False
