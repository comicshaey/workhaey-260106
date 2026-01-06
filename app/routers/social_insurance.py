from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from starlette.background import BackgroundTask

from app.core.config import settings
from app.core.tempfiles import new_job_dir, ensure_dir, cleanup_old
from app.services.social_insurance_service import build_raw_dataframe
from app.services.excel_writer import write_social_insurance_xlsx

router = APIRouter(prefix="/modules/social-insurance", tags=["social-insurance"])

@router.get("", response_class=HTMLResponse)
def social_insurance_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "modules_social_insurance.html",
        {"request": request},
    )

def _save_upload(job_dir: Path, up: UploadFile | None, name: str) -> Path | None:
    if up is None:
        return None
    p = job_dir / name
    with p.open("wb") as f:
        f.write(up.file.read())
    return p

@router.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    pension: UploadFile | None = File(default=None),
    health: UploadFile | None = File(default=None),
    emp_worker: UploadFile | None = File(default=None),
    ia_worker: UploadFile | None = File(default=None),
    emp_labor: UploadFile | None = File(default=None),
    ia_labor: UploadFile | None = File(default=None),
):
    ensure_dir(settings.TMP_DIR)
    cleanup_old(settings.TMP_DIR, ttl_seconds=60*30)

    job_dir = new_job_dir(settings.TMP_DIR)

    # 업로드 저장
    pension_p = _save_upload(job_dir, pension, "근로자_국민연금.pdf")
    health_p = _save_upload(job_dir, health, "근로자_건강보험.pdf")
    empw_p = _save_upload(job_dir, emp_worker, "근로자_고용보험.pdf")
    iaw_p = _save_upload(job_dir, ia_worker, "근로자_산재보험.pdf")
    empl_p = _save_upload(job_dir, emp_labor, "노무제공자_고용보험.pdf")
    ial_p = _save_upload(job_dir, ia_labor, "노무제공자_산재보험.pdf")

    # 최소 입력 체크(근로자든 노무제공자든 뭐라도 하나는 있어야 함)
    if not any([pension_p, health_p, empw_p, iaw_p, empl_p, ial_p]):
        return request.app.state.templates.TemplateResponse(
            "modules_social_insurance_result.html",
            {
                "request": request,
                "ok": False,
                "message": "업로드된 파일이 없습니다. 최소 1개 PDF는 올려야 합니다.",
                "download_url": None,
            },
        )

    # RAW DF 생성
    raw_df = build_raw_dataframe(
        pension_pdf=pension_p,
        health_pdf=health_p,
        emp_worker_pdf=empw_p,
        ia_worker_pdf=iaw_p,
        emp_labor_pdf=empl_p,
        ia_labor_pdf=ial_p,
    )

    # 엑셀 생성
    out_xlsx = job_dir / "사회보험료_통합산출.xlsx"
    write_social_insurance_xlsx(raw_df, out_xlsx, title="사회보험료 통합 산출(업로드 PDF 기반)")

    download_url = f"/modules/social-insurance/download/{job_dir.name}/사회보험료_통합산출.xlsx"

    return request.app.state.templates.TemplateResponse(
        "modules_social_insurance_result.html",
        {
            "request": request,
            "ok": True,
            "message": "엑셀 생성 완료. 다운로드 버튼을 눌러 받으세요.",
            "download_url": download_url,
        },
    )

def _delete_job_dir(job_dir: Path):
    # 다운로드 후 파일 흔적 최소화(한 번 받으면 끝)
    try:
        for child in sorted(job_dir.rglob("*"), reverse=True):
            try:
                if child.is_file():
                    child.unlink(missing_ok=True)
                elif child.is_dir():
                    child.rmdir()
            except Exception:
                pass
        try:
            job_dir.rmdir()
        except Exception:
            pass
    except Exception:
        pass

@router.get("/download/{job_id}/{filename}")
def download(job_id: str, filename: str):
    job_dir = settings.TMP_DIR / job_id
    file_path = job_dir / filename
    if not file_path.exists():
        # 파일이 이미 삭제됐거나 잘못된 요청
        return {"error": "file not found"}

    # 다운로드 끝나면 백그라운드로 삭제
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(_delete_job_dir, job_dir),
    )
