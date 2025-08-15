import json

FALLBACK_TEXT = "Sorry, something went wrong."
FALLBACK_AUDIO = b""  # empty bytes for failed audio

def structured_error(exception: Exception, fallback):
    """Return fallback value with error logging."""
    print(f"[ERROR] {exception}")
    return fallback
