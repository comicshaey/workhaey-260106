import re
from collections import defaultdict
from pathlib import Path
from .common import extract_text

def parse_emp_worker(pdf_path: Path) -> list[dict]:
    """
    근로자 고용보험:
    - 근로자실업급여보험료(개인)
    - 사업주실업급여보험료(기관)
    - 사업주고안직능보험료(기관)
    - 개인별 소계(합계)
    """
    text = extract_text(pdf_path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    rows = defaultdict(
        lambda: {
            "성명": None,
            "고용_개인실업": 0,
            "고용_기관실업": 0,
            "고용_기관고안직능": 0,
            "고용_합계": 0,
        }
    )

    current = None
    for ln in lines:
        m = re.match(r"^(\d+)\s+일반\s+([가-힣]{2,4})\s+\d{2}-\d{2}-\d{2}", ln)
        if m:
            current = m.group(2)
            rows[current]["성명"] = current
            continue

        if not current:
            continue

        if "근로자실업급여보험료" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if nums:
                rows[current]["고용_개인실업"] = int(nums[-1].replace(",", ""))
        elif "사업주실업급여보험료" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if nums:
                rows[current]["고용_기관실업"] = int(nums[-1].replace(",", ""))
        elif "사업주고안직능보험료" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if nums:
                rows[current]["고용_기관고안직능"] = int(nums[-1].replace(",", ""))
        elif "개인별 소계" in ln or "개인별소계" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if nums:
                rows[current]["고용_합계"] = int(nums[-1].replace(",", ""))

    return [v for v in rows.values() if v["성명"]]
