import os
import time
import uuid
from pathlib import Path
from typing import Iterable

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def new_job_dir(base: Path) -> Path:
    job_id = f"{int(time.time())}_{uuid.uuid4().hex[:10]}"
    d = base / job_id
    ensure_dir(d)
    return d

def cleanup_old(base: Path, ttl_seconds: int = 60 * 30) -> int:
    """
    오래된 임시 폴더 삭제(기본 30분). 운영시 크론/스케줄러로 돌려도 되고,
    요청 들어올 때마다 가볍게 호출해도 됨.
    """
    if not base.exists():
        return 0
    now = time.time()
    deleted = 0
    for p in base.iterdir():
        try:
            if not p.is_dir():
                continue
            mtime = p.stat().st_mtime
            if now - mtime > ttl_seconds:
                for child in p.rglob("*"):
                    try:
                        if child.is_file():
                            child.unlink(missing_ok=True)
                    except Exception:
                        pass
                try:
                    p.rmdir()
                except Exception:
                    # 비어있지 않으면 한번 더
                    for child in sorted(p.rglob("*"), reverse=True):
                        try:
                            if child.is_dir():
                                child.rmdir()
                        except Exception:
                            pass
                    try:
                        p.rmdir()
                    except Exception:
                        pass
                deleted += 1
        except Exception:
            pass
    return deleted
