import re
from pathlib import Path
from .common import extract_text

def parse_emp_labor(pdf_path: Path) -> list[dict]:
    """
    노무제공자(방과후강사) 고용보험:
    텍스트 추출 특성상 "근로자실업급여보험료/사업주실업급여보험료/개인별소계"가 먼저 나오고,
    그 다음에 "N 특수() 성명" 라인이 나오는 형태가 흔함.
    => 직전에 읽어둔 금액을 해당 성명에 붙여서 행 생성.
    """
    text = extract_text(pdf_path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    rows = []
    tmp_emp = None
    tmp_org = None
    tmp_sum = None

    for ln in lines:
        if "근로자실업급여보험료" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if len(nums) >= 2:
                tmp_emp = int(nums[1].replace(",", ""))  # 현재년도(②) 금액
        elif "사업주실업급여보험료" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if len(nums) >= 2:
                tmp_org = int(nums[1].replace(",", ""))
        elif "개인별소계" in ln or "개인별 소계" in ln:
            nums = re.findall(r"-?\d[\d,]*", ln)
            if len(nums) >= 2:
                tmp_sum = int(nums[1].replace(",", ""))

        m = re.match(r"^\d+\s+특수\(\)\s+([가-힣]{2,4})\s+\d{2}-\d{2}-\d{2}", ln)
        if m:
            name = m.group(1)
            emp = tmp_emp or 0
            org = tmp_org or 0
            s = tmp_sum if tmp_sum is not None else emp + org

            rows.append(
                {"성명": name, "노무고용_개인": emp, "노무고용_기관": org, "노무고용_합계": s}
            )
            tmp_emp = tmp_org = tmp_sum = None

    return rows
