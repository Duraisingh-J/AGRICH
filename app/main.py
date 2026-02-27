"""Root-level ASGI entrypoint shim.

This allows deployment commands like:
    uvicorn app.main:app
to work even when the repository root is used as the working directory.
"""

from backend.app.main import app
