import json
import os


class ConfigError(Exception):
    """Raised with a message meant to be shown directly to the person running the installer."""
    pass


def load_config(path):
    """
    Loads and validates config.json. This exists as a single shared
    function (instead of a bare json.load() in four different scripts)
    because of a real bug: on Windows, PowerShell's
    `Out-File -Encoding utf8` always writes a UTF-8 byte-order-mark, which
    Python's default json.load() does not skip - it saw invisible BOM
    bytes before "{" and failed with:
        JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    encoding="utf-8-sig" strips a BOM if present and is identical to plain
    utf-8 if there isn't one, so this is safe for every installer
    (Linux/macOS/Windows) regardless of how config.json was written.
    """
    if not os.path.exists(path):
        raise ConfigError(
            f"Config file not found at {path}. The installer may not have finished - re-run the install command."
        )

    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            raw = f.read()
    except OSError as e:
        raise ConfigError(f"Could not read config file at {path}: {e}")

    if not raw.strip():
        raise ConfigError(
            f"Config file at {path} is empty. The installer likely failed partway through writing it - re-run the install command."
        )

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"Config file at {path} is not valid JSON ({e}). Delete it and re-run the install command to regenerate it."
        )

    required = ["server_url", "agent_id", "token"]
    missing = [k for k in required if k not in config or config[k] in (None, "")]
    if missing:
        raise ConfigError(
            f"Config file at {path} is missing required field(s): {', '.join(missing)}. Re-run the install command."
        )

    return config
