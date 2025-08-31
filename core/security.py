import hashlib, hmac, secrets

def _pbkdf2_hash(password: str, salt: bytes = None, iterations: int = 200_000):
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations, dklen=32)
    return salt, digest, iterations

def hash_password(password: str) -> str:
    salt, digest, iters = _pbkdf2_hash(password)
    return f"pbkdf2_sha256${iters}${salt.hex()}${digest.hex()}"

def check_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$", 3)
        assert algo == "pbkdf2_sha256"
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        _, candidate, _ = _pbkdf2_hash(password, salt=salt, iterations=int(iters))
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False