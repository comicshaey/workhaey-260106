import re
from pathlib import Path
from .common import extract_text

def parse_ia_labor(pdf_path: Path) -> list[dict]:
    """
    노무제공자 산재: 합계만 나오면 개인/기관 1/2로 분배(표 서식 기준)
    """
    text = extract_text(pdf_path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    rows = []
    for ln in lines:
        m = re.match(
            r"^\d+\s+제공자\(\s*([가-힣]{2,4})\s+\d{2}-\d{2}-\d{2}\s+0\s+0\s+([\d,]+)\s+0\s+0\s+([\d,]+)\s*$",
            ln,
        )
        if m:
            name = m.group(1)
            total = int(m.group(2).replace(",", ""))
            emp = total // 2
            org = total - emp
            rows.append(
                {"성명": name, "노무산재_개인": emp, "노무산재_기관": org, "노무산재_합계": total}
            )
    return rows
