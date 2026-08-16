from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set

from fastapi import Depends, UploadFile

from app.config import Settings
from app.core.exceptions import AppError, NotFoundError
from app.dependencies import get_app_settings


DEFAULT_ALLOWED_ARTIFACT_CONTENT_TYPES = {
    "application/gzip",
    "application/x-gzip",
    "application/zip",
    "application/x-tar",
    "application/octet-stream",
}


class ArtifactStorageError(AppError):
    """Base error raised by the local artifact storage backend."""


class UnsupportedArtifactTypeError(ArtifactStorageError):
    def __init__(self, message: str = "Unsupported artifact content type"):
        super().__init__(message, status_code=422)


class ArtifactTooLargeError(ArtifactStorageError):
    def __init__(self, message: str = "Artifact file is too large"):
        super().__init__(message, status_code=413)


class EmptyArtifactError(ArtifactStorageError):
    def __init__(self, message: str = "Artifact file must not be empty"):
        super().__init__(message, status_code=422)


@dataclass(frozen=True)
class StoredArtifact:
    storage_path: str
    size_bytes: int
    checksum: str
    filename: str
    content_type: str


def _content_types(value: str) -> Set[str]:
    return {
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    }


class LocalArtifactStorage:
    def __init__(
        self,
        root: str,
        max_size_bytes: int = 100 * 1024 * 1024,
        allowed_content_types: Optional[Set[str]] = None,
    ) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = int(max_size_bytes)
        self.allowed_content_types = set(
            allowed_content_types or DEFAULT_ALLOWED_ARTIFACT_CONTENT_TYPES
        )

    def _safe_filename(self, filename: Optional[str]) -> str:
        raw_name = Path(filename or "artifact").name
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name)
        safe_name = safe_name.strip(" .")
        if not safe_name:
            safe_name = "artifact"

        suffix = Path(safe_name).suffix[:16]
        stem = Path(safe_name).stem
        max_stem_length = 160 - len(suffix)
        if len(stem) > max_stem_length:
            stem = stem[:max_stem_length]
        return f"{stem}{suffix}" if suffix else stem

    def _validate_content_type(self, content_type: Optional[str]) -> str:
        normalized = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized not in self.allowed_content_types:
            raise UnsupportedArtifactTypeError()
        return normalized

    def _ensure_inside_root(self, target: Path) -> Path:
        try:
            target.relative_to(self.root)
        except ValueError:
            raise NotFoundError("Artifact file not found")
        return target

    async def save(
        self,
        upload_file: UploadFile,
        project_id: uuid.UUID,
        repository_id: uuid.UUID,
    ) -> StoredArtifact:
        content_type = self._validate_content_type(upload_file.content_type)
        filename = self._safe_filename(upload_file.filename)
        relative_path = Path(str(project_id)) / str(repository_id) / f"{uuid.uuid4().hex}-{filename}"
        target = self._ensure_inside_root((self.root / relative_path).resolve())
        target.parent.mkdir(parents=True, exist_ok=True)

        hasher = hashlib.sha256()
        size_bytes = 0
        try:
            with target.open("wb") as output:
                while True:
                    chunk = await upload_file.read(1024 * 1024)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        raise ArtifactTooLargeError()
                    hasher.update(chunk)
                    output.write(chunk)
        except Exception:
            try:
                target.unlink()
            except FileNotFoundError:
                pass
            raise

        if size_bytes == 0:
            target.unlink()
            raise EmptyArtifactError()

        return StoredArtifact(
            storage_path=str(relative_path),
            size_bytes=size_bytes,
            checksum=hasher.hexdigest(),
            filename=filename,
            content_type=content_type,
        )

    def resolve(self, storage_path: str) -> Path:
        relative = Path(storage_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise NotFoundError("Artifact file not found")
        target = self._ensure_inside_root((self.root / relative).resolve())
        if not target.is_file():
            raise NotFoundError("Artifact file not found")
        return target

    async def delete(self, storage_path: str) -> None:
        try:
            target = self.resolve(storage_path)
        except NotFoundError:
            return
        try:
            target.unlink()
        except FileNotFoundError:
            pass


def get_artifact_storage(settings: Settings = Depends(get_app_settings)) -> LocalArtifactStorage:
    return LocalArtifactStorage(
        root=settings.artifact_storage_root,
        max_size_bytes=settings.artifact_max_size_bytes,
        allowed_content_types=_content_types(settings.artifact_allowed_content_types),
    )
