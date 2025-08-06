import time

otp_store = {}

def set_otp(email: str, otp: str, ttl_seconds: int = 600):
    expiry = time.time() + ttl_seconds
    otp_store[email] = {
        "otp": otp,
        "expires_at": expiry,
    }

def verify_otp(email: str, otp: str) -> bool:
    record = otp_store.get(email)
    if not record:
        return False
    if time.time() > record["expires_at"]:
        del otp_store[email]
        return False
    if record["otp"] != otp:
        return False
    del otp_store[email]
    return True