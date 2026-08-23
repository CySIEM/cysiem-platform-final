import os


def get_backend():
    backend = os.getenv("DETECTION_BACKEND", "ollama").lower()
    if backend == "ollama":
        from .ollama_backend import infer

        return infer
    if backend == "transformers":
        from .transformers_backend import infer

        return infer
    raise ValueError(f"Unknown DETECTION_BACKEND: {backend!r} (expected 'ollama' or 'transformers')")
