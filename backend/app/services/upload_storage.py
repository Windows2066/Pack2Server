from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.paths import data_root


async def save_upload(file: UploadFile) -> tuple[str, Path, int]:
    upload_id = uuid4().hex
    filename = file.filename or "upload.bin"
    target = data_root() / "uploads" / f"{upload_id}-{Path(filename).name}"
    target.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    with target.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > get_settings().max_upload_bytes:
                target.unlink(missing_ok=True)
                raise ValueError("上传文件超过大小限制")
            handle.write(chunk)
    return upload_id, target, size
