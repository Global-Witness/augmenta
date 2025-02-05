import json
import hashlib

def get_config_hash(config: dict) -> str:
    """Generate deterministic hash of config data"""
    return hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()
    ).hexdigest()