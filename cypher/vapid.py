"""Prints a fresh VAPID key pair. Put the values into your host's secrets, never into git."""
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

k = ec.generate_private_key(ec.SECP256R1())
b = lambda x: base64.urlsafe_b64encode(x).decode().rstrip('=')
priv = b(k.private_numbers().private_value.to_bytes(32, 'big'))
pub = b(k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint))
print('VAPID_PRIVATE_KEY=' + priv)
print('VAPID_PUBLIC_KEY=' + pub)
print('SECRET_KEY=' + base64.urlsafe_b64encode(__import__('os').urandom(32)).decode())
