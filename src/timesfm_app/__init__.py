"""Local-first TimesFM forecasting application."""

import os

# Windows commonly lacks symlink privileges. Hugging Face's supported fallback avoids
# its symlink probe and stores snapshot copies instead.
if os.name == "nt":
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
