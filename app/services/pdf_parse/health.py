import re
from collections import defaultdict
from pathlib import Path
from .common import extract_text

_BAD_TOKENS = {
    "건강", "요양", "총계", "장기", "국민", "사업", "직장", "구분", "고지", "산출",
    "부과", "출력", "페이지", "관리", "번호", "보험", "료", "정산", "환급",
}

def parse_health(pdf_path: Path) -> list[dict]:
    """
    건강보험/장기요양: 각 라인의 끝 금액(고지보험료)을 잡아서 개인=기관으로 채움.
    PDF 텍스트 추출이 줄바꿈을 깨뜨릴 수 있어 '완벽 파서'는 아니고,
    운영하면서 케이스별 보강하는 방식이 현실적.
    """
    text = extract_text(pdf_path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    rows = defaultdict(
        lambda: {
            "성명": None,
            "건강_개인": 0,
            "건강_기관": 0,
            "건강_합계": 0,
            "요양_개인": 0,
            "요양_기관": 0,
            "요양_합계": 0,
        }
    )

    for ln in lines:
        # 이름 후보
        nm = re.search(r"\s([가-힣]{2,4})\s", " " + ln + " ")
        if not nm:
            continue
        name = nm.group(1)
        if name in _BAD_TOKENS:
            continue

        is_health = bool(re.search(r"건\s*강|\b건\b|건강", ln))
        is_care = bool(re.search(r"요\s*양|\b요\b|요양", ln))
        if not (is_health or is_care):
            continue

        nums = re.findall(r"-?\d[\d,]*", ln)
        if not nums:
            continue
        amt = int(nums[-1].replace(",", ""))

        rec = rows[name]
        rec["성명"] = name

        # 건강 라인 / 요양 라인 분리
        if is_health and not is_care:
            rec["건강_개인"] = amt
            rec["건강_기관"] = amt
            rec["건강_합계"] = amt * 2
        elif is_care and not is_health:
            rec["요양_개인"] = amt
            rec["요양_기관"] = amt
            rec["요양_합계"] = amt * 2

    return [v for v in rows.values() if v["성명"]]
