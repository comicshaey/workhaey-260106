from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return request.app.state.templates.TemplateResponse(
        "index.html",
        {"request": request},
    )

@router.get("/modules", response_class=HTMLResponse)
def modules(request: Request):
    modules = [
        {
            "key": "social-insurance",
            "title": "사회보험료 고지내역 PDF → 엑셀 변환",
            "desc": "근로자(연금/건강·요양/고용/산재) + 노무제공자(고용/산재) 통합 후 시트 분리",
            "href": "/modules/social-insurance",
            "tag": "인사·급여·복무",
        },
        # 앞으로 여기 계속 추가
    ]
    return request.app.state.templates.TemplateResponse(
        "modules.html",
        {"request": request, "modules": modules},
    )
