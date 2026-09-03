"""Content-addressed blob storage for PDFs, images, DOCX and large text."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    def put(self, data: bytes, suffix: str = "") -> str: ...
    def put_file(self, path: Path) -> str: ...
    def get(self, key: str) -> bytes: ...
    def path(self, key: str) -> Path: ...
    def exists(self, key: str) -> bool: ...


class LocalBlobStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _key(self, data: bytes, suffix: str) -> str:
        digest = hashlib.sha256(data).hexdigest()
        return f"{digest}{suffix}"

    def put(self, data: bytes, suffix: str = "") -> str:
        key = self._key(data, suffix)
        target = self.root / key
        if not target.exists():
            tmp = target.with_suffix(target.suffix + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(target)
        return key

    def put_file(self, path: Path) -> str:
        path = Path(path)
        return self.put(path.read_bytes(), suffix=path.suffix)

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def path(self, key: str) -> Path:
        return self.root / key

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()

    def copy_to(self, key: str, dest: Path) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.root / key, dest)
        return dest
