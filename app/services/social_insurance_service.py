from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import pandas as pd

from .pdf_parse.pension import parse_pension
from .pdf_parse.health import parse_health
from .pdf_parse.emp_worker import parse_emp_worker
from .pdf_parse.ia_worker import parse_ia_worker
from .pdf_parse.emp_labor import parse_emp_labor
from .pdf_parse.ia_labor import parse_ia_labor

WORKER_COLS = [
    "국민연금_개인","국민연금_기관","국민연금_합계",
    "건강_개인","건강_기관","건강_합계",
    "요양_개인","요양_기관","요양_합계",
    "고용_개인실업","고용_기관실업","고용_기관고안직능","고용_합계",
    "산재_기관","산재_합계",
]

LABOR_COLS = [
    "노무고용_개인","노무고용_기관","노무고용_합계",
    "노무산재_개인","노무산재_기관","노무산재_합계"
]

def _merge(master: dict, rows: list[dict]) -> None:
    for r in rows:
        name = r["성명"]
        master[name]["성명"] = name
        master[name].update(r)

def build_raw_dataframe(
    pension_pdf: Path | None,
    health_pdf: Path | None,
    emp_worker_pdf: Path | None,
    ia_worker_pdf: Path | None,
    emp_labor_pdf: Path | None,
    ia_labor_pdf: Path | None,
) -> pd.DataFrame:
    # 1) 근로자 그룹
    master = defaultdict(dict)

    if pension_pdf:
        _merge(master, parse_pension(pension_pdf))
    if health_pdf:
        _merge(master, parse_health(health_pdf))
    if emp_worker_pdf:
        _merge(master, parse_emp_worker(emp_worker_pdf))
    if ia_worker_pdf:
        _merge(master, parse_ia_worker(ia_worker_pdf))

    # 빈값 채우기
    for rec in master.values():
        for c in WORKER_COLS:
            rec.setdefault(c, 0)

    df_worker = pd.DataFrame(list(master.values()))
    if not df_worker.empty:
        df_worker = df_worker.sort_values("성명")
        df_worker["구분"] = "근로자4대"
        # 국민연금/건강/요양/고용이 전부 0인데 산재만 있으면 산재만으로 분류
        mask_only_ia = (
            df_worker[["국민연금_합계","건강_합계","요양_합계","고용_합계"]].sum(axis=1) == 0
        ) & (df_worker["산재_합계"] > 0)
        df_worker.loc[mask_only_ia, "구분"] = "산재만"

        df_worker["개인합계"] = df_worker[["국민연금_개인","건강_개인","요양_개인","고용_개인실업"]].sum(axis=1)
        df_worker["기관합계"] = df_worker[["국민연금_기관","건강_기관","요양_기관","고용_기관실업","고용_기관고안직능","산재_기관"]].sum(axis=1)
        df_worker["총계"] = df_worker["개인합계"] + df_worker["기관합계"]

    # 2) 노무제공자 그룹
    labor_master = defaultdict(dict)
    if emp_labor_pdf:
        _merge(labor_master, parse_emp_labor(emp_labor_pdf))
    if ia_labor_pdf:
        _merge(labor_master, parse_ia_labor(ia_labor_pdf))

    for rec in labor_master.values():
        for c in LABOR_COLS:
            rec.setdefault(c, 0)

    df_labor = pd.DataFrame(list(labor_master.values()))
    if not df_labor.empty:
        df_labor = df_labor.sort_values("성명")
        df_labor["구분"] = "방과후(노무제공자)"
        df_labor["개인합계"] = df_labor[["노무고용_개인","노무산재_개인"]].sum(axis=1)
        df_labor["기관합계"] = df_labor[["노무고용_기관","노무산재_기관"]].sum(axis=1)
        df_labor["총계"] = df_labor["개인합계"] + df_labor["기관합계"]

    # 3) RAW 통합 컬럼으로 맞추기
    raw_cols = [
        "구분","성명",
        "국민연금_개인","국민연금_기관",
        "건강_개인","건강_기관",
        "요양_개인","요양_기관",
        "고용_개인실업","고용_기관실업","고용_기관고안직능",
        "산재_기관",
        "개인합계","기관합계","총계",
    ]

    if df_worker.empty:
        df_worker = pd.DataFrame(columns=raw_cols)

    # labor를 raw 스키마로 매핑
    if not df_labor.empty:
        df_lr = df_labor.copy()
        df_lr["국민연금_개인"] = 0
        df_lr["국민연금_기관"] = 0
        df_lr["건강_개인"] = 0
        df_lr["건강_기관"] = 0
        df_lr["요양_개인"] = 0
        df_lr["요양_기관"] = 0
        df_lr["고용_개인실업"] = df_lr["노무고용_개인"]
        df_lr["고용_기관실업"] = df_lr["노무고용_기관"]
        df_lr["고용_기관고안직능"] = 0
        df_lr["산재_기관"] = df_lr["노무산재_기관"]
        df_labor_raw = df_lr[raw_cols].copy()
    else:
        df_labor_raw = pd.DataFrame(columns=raw_cols)

    raw_all = pd.concat([df_worker[raw_cols], df_labor_raw], ignore_index=True)
    raw_all = raw_all.sort_values(["구분","성명"]).reset_index(drop=True)
    return raw_all
