"""
WordPress JWT authentication helpers for the Danger Finger Tornado server.

The WordPress site uses the "JWT Authentication for WP REST API" plugin.
Tokens are issued at /wp-json/jwt-auth/v1/token and validated here locally
using the shared JWT_AUTH_SECRET_KEY (env var: jwt_secret).

The WP site must add user_nicename to the JWT payload via:
    add_filter('jwt_auth_token_before_sign', ...) — see functions-auth.php.
Tornado uses user_nicename as the profile key for S3 reads/writes.
"""
import os
import hashlib
import time
from threading import Lock

try:
    import jwt as pyjwt
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

JWT_SECRET = os.environ.get("jwt_secret", "")
_AUTH_DISABLED = not JWT_SECRET

# In-memory token cache to avoid re-decoding every request.
# Key: sha256(token)[:32], Value: (payload_dict, expiry_epoch)
_cache: dict = {}
_cache_lock = Lock()
_CACHE_TTL = 300  # seconds; tokens are re-verified after this


def _ck(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:32]


def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and entry[1] > time.time():
            return entry[0]
        if entry:
            del _cache[key]
    return None


def _cache_set(key: str, payload: dict):
    with _cache_lock:
        if len(_cache) > 500:
            now = time.time()
            stale = [k for k, (_, exp) in list(_cache.items()) if exp <= now]
            for k in stale:
                _cache.pop(k, None)
        _cache[key] = (payload, time.time() + _CACHE_TTL)


def validate_jwt(token: str):
    """Decode and verify a WordPress JWT token.

    Returns the payload dict on success, None on failure.
    In dev mode (jwt_secret not set), accepts any Bearer token and returns
    a guest payload — never do this in production.
    """
    if not token:
        return None

    ck = _ck(token)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    if _AUTH_DISABLED:
        print("WARNING: jwt_secret not configured — auth disabled (dev mode only)")
        payload = {"data": {"user": {"id": "0", "user_nicename": "dev", "user_display_name": "Dev User"}}}
        _cache_set(ck, payload)
        return payload

    if not _JWT_AVAILABLE:
        print("ERROR: PyJWT not installed — run: pip install 'PyJWT>=2.0'")
        return None

    try:
        payload = pyjwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # jwt-auth plugin does not set audience
        )
        _cache_set(ck, payload)
        return payload
    except pyjwt.ExpiredSignatureError:
        print("JWT: token expired")
    except pyjwt.InvalidTokenError as exc:
        print("JWT: invalid token — %s" % exc)
    return None


def get_nicename(payload: dict) -> str:
    """Extract user_nicename from a validated JWT payload.

    Requires the WP jwt_auth_token_before_sign filter (functions-auth.php)
    to embed user_nicename in payload['data']['user']['user_nicename'].
    Falls back to 'user_{id}' when the filter is not installed.
    """
    if not payload:
        return "unknown"
    user = payload.get("data", {}).get("user", {})
    nicename = user.get("user_nicename")
    if nicename:
        return nicename
    uid = user.get("id", "0")
    return "user_%s" % uid
