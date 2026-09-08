#!/usr/bin/env python3
"""Atomic same-directory writes for authored and generated project outputs."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Flush a uniquely named sibling file before replacing the destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    """Atomically write UTF-8 text whose newline policy is set by the caller."""
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(
    path: Path, document: Any, *, ensure_ascii: bool = True
) -> None:
    """Serialize deterministic indented JSON through the atomic byte writer."""
    atomic_write_text(
        path,
        json.dumps(document, ensure_ascii=ensure_ascii, indent=2) + "\n",
    )
