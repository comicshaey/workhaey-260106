import re
from pathlib import Path
from .common import extract_text

def parse_pension(pdf_path: Path) -> list[dict]:
    """
    국민연금: 행 끝의 '고지보험료'만 뽑아서 개인/기관 1/2로 분배(직장가입자 표 기준)
    """
    text = extract_text(pdf_path)
    rows = []
    pat = re.compile(
        r"^\s*(\d+)\s+\d+\s+\d{6}-\d\*+\s+([가-힣]+)\s+\d+\s+\d{4}\.\d{2}\s+~\s+\d{4}\.\d{2}\s+([\d,]+)\s*$",
        re.M,
    )
    for m in pat.finditer(text):
        name = m.group(2)
        total = int(m.group(3).replace(",", ""))
        emp = total // 2
        org = total - emp
        rows.append(
            {
                "성명": name,
                "국민연금_개인": emp,
                "국민연금_기관": org,
                "국민연금_합계": total,
            }
        )
    return rows
