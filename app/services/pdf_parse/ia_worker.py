import re
from collections import defaultdict
from pathlib import Path
from .common import extract_text

def parse_ia_worker(pdf_path: Path) -> list[dict]:
    """
    근로자 산재보험: 보통 기관 부담만 있음(산재_기관=산재_합계)
    """
    text = extract_text(pdf_path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    rows = defaultdict(lambda: {"성명": None, "산재_기관": 0, "산재_합계": 0})

    for ln in lines:
        m = re.match(
            r"^\d+\s+일반\s+([가-힣]{2,4})\s+\d{2}-\d{2}-\d{2}\s+\d{4}-\d{2}-\d{2}.*\s(-?\d[\d,]*)\s+0\s+0\s+0\s+(-?\d[\d,]*)\s*$",
            ln,
        )
        if m:
            name = m.group(1)
            amt = int(m.group(2).replace(",", ""))
            rows[name]["성명"] = name
            rows[name]["산재_기관"] = amt
            rows[name]["산재_합계"] = amt

    return [v for v in rows.values() if v["성명"]]
