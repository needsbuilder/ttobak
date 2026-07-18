"""Adversarial reproducers for the Fidelity gate (final-review M1/M2).

These exercise the REAL ``verify()`` over a REAL ``Document`` with adversarial
easy-text rewrites that are demo-able false-negatives in the headline safety
gate. Each "flip" must NOT pass (route to HUMAN_REVIEW, since the meaning change
is unsafe and not auto-recoverable); each faithful CONTROL must PASS.

M1 = date inclusivity (까지 vs 전에/이전에) flip.
M2 = eligibility boundary operators (이상/초과/이하/미만).
"""
from datetime import date

from ttobak.common import Verdict
from ttobak.fidelity import verify
from ttobak.fidelity.models import SlotType
from ttobak.ir import Block, BlockType, Document

REF = date(2026, 7, 1)


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)], source_mime="text/plain")


# ---------------------------------------------------------------------------
# M1 — date inclusivity (까지 vs 전에/이전에) flip is unsafe -> HUMAN_REVIEW
# ---------------------------------------------------------------------------

_M1_SOURCE = "건강보험료를 2026년 7월 17일까지 납부하세요."


def test_m1_kkaji_to_jeone_is_human_review():
    # "까지" (inclusive of the 17th) -> "전에" (before the 17th): deadline meaning flip.
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일 전에 내세요.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m1_kkaji_to_ijeone_is_human_review():
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일 이전에 내세요.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m1_kkaji_dropped_bare_date_not_pass():
    # "까지" dropped entirely (bare date): inclusivity boundary lost -> must not PASS.
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일 내세요.", REF)
    assert report.verdict != Verdict.PASS


def test_m1_faithful_kkaji_control_passes_for_date():
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일까지 내세요.", REF)
    assert report.verdict == Verdict.PASS
    # the date slot itself must not be among the failures
    assert not any(s.type == SlotType.DATE for s in report.failed_slots)


# ---------------------------------------------------------------------------
# M2 — eligibility boundary operators
#   faithful copies must PASS; operator flips must -> HUMAN_REVIEW
# ---------------------------------------------------------------------------

def test_m2_faithful_isang_passes():
    src = "만 65세 이상만 신청 가능합니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS
    assert not any(s.type == SlotType.SCOPE for s in report.failed_slots)


def test_m2_faithful_miman_passes():
    src = "소득 100만원 미만 가구가 대상입니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS
    assert not any(s.type == SlotType.SCOPE for s in report.failed_slots)


def test_m2_faithful_chogwa_passes():
    src = "정원 100명 초과 시 마감합니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS
    assert not any(s.type == SlotType.SCOPE for s in report.failed_slots)


def test_m2_isang_to_iha_flip_is_human_review():
    src = "만 65세 이상만 신청 가능합니다."
    easy = "만 65세 이하만 신청할 수 있어요."
    report = verify(_doc(src), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m2_miman_to_iha_flip_is_human_review():
    src = "소득 100만원 미만 가구가 대상입니다."
    easy = "소득 100만원 이하 가구가 대상이에요."
    report = verify(_doc(src), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m2_boundary_dropped_in_easy_is_caught():
    # Boundary keyword dropped entirely from easy text: meaning lost while the
    # operand "65세" is preserved -> unsafe flip -> HUMAN_REVIEW.
    src = "만 65세 이상만 신청 가능합니다."
    easy = "만 65세 신청 가능합니다."
    report = verify(_doc(src), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW
    assert report.drift_flags


# ---------------------------------------------------------------------------
# Regression — the money-shot must still work
# ---------------------------------------------------------------------------

def test_money_shot_rounding_revises():
    src = _doc("보험료 1,295,400원을 납부하세요.")
    report = verify(src, "이번 달 보험료는 약 130만 원입니다.", REF)
    assert report.verdict == Verdict.REVISE
    assert any(s.normalized_value == "1295400" for s in report.failed_slots)


def test_money_shot_exact_passes():
    src = _doc("보험료 1,295,400원을 납부하세요.")
    report = verify(src, "이번 달 보험료는 1,295,400원입니다.", REF)
    assert report.verdict == Verdict.PASS


# ---------------------------------------------------------------------------
# M3 — comma-grouped numeric thresholds (콤마 숫자 자격 경계)
#   기존 _SCOPE_RE가 콤마에서 오퍼랜드를 절단해(예: '30,000원'→'000원')
#   임계값 변경이 통과되고, 무손상 페어가 오탐되는 게이트 구멍의 회귀 테스트.
# ---------------------------------------------------------------------------

_M3_SOURCE = "인구 30,000명 이상인 지역만 지원 대상입니다."


def test_m3_scope_raw_span_keeps_comma_operand():
    from ttobak.fidelity.extract import extract_slots
    slots = extract_slots(_doc(_M3_SOURCE), REF)
    scopes = [s for s in slots if s.type == SlotType.SCOPE]
    assert scopes, "SCOPE slot must be extracted"
    assert any("30,000명" in s.raw_span for s in scopes), (
        f"comma operand truncated: {[s.raw_span for s in scopes]}")


def test_m3_comma_threshold_value_change_not_pass():
    # 30,000명 -> 50,000명: 자격 임계값 변경. 절단된 '000명'이 우연히 살아남아
    # PASS 되면 안 된다 (MONEY 슬롯이 없는 '명' 단위로 격리).
    report = verify(_doc(_M3_SOURCE), "인구 50,000명 이상인 지역만 지원 대상입니다.", REF)
    assert report.verdict != Verdict.PASS


def test_m3_identical_two_comma_thresholds_pass():
    # 서로 다른 두 콤마 임계값이 있는 문서의 '완전 동일' 쉬운본은 반드시 PASS.
    # (절단된 오퍼랜드끼리 첫 출현으로 뭉개지면 무손상 페어가 HUMAN_REVIEW 오탐됨)
    src = "지원금은 5,000원 이상이며, 자격은 30,000원 미만인 사람만 해당합니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


def test_m3_comma_operator_flip_still_human_review():
    report = verify(_doc(_M3_SOURCE), "인구 30,000명 미만인 지역만 지원 대상입니다.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m3_scope_operand_no_substring_cross_match():
    # '5,000명 이상'이 '15,000명 이상' 안의 부분문자열로 생존 처리되면 안 된다.
    src = "정원이 5,000명 이상이어야 합니다."
    report = verify(_doc(src), "정원이 15,000명 이상이어야 합니다.", REF)
    assert report.verdict != Verdict.PASS


# ---------------------------------------------------------------------------
# M4 — same-operand multi-threshold drift (동일 오퍼랜드 복수 경계)
# ---------------------------------------------------------------------------

_M4_SOURCE = "만 65세 미만인 사람은 A지원금을, 만 65세 이상인 사람은 B지원금을 신청합니다."


def test_m4_faithful_same_operand_pair_passes():
    # 동일 오퍼랜드(65세)가 서로 다른 연산자로 두 번 나오는 문서의 무손상 쉬운본은
    # PASS여야 한다. (첫 출현만 검사하면 두 번째 슬롯이 첫 연산자와 비교돼 오탐)
    report = verify(_doc(_M4_SOURCE), _M4_SOURCE, REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


def test_m4_second_threshold_flip_is_human_review():
    easy = "만 65세 미만인 사람은 A지원금을, 만 65세 미만인 사람은 B지원금을 신청합니다."
    report = verify(_doc(_M4_SOURCE), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


# ---------------------------------------------------------------------------
# M5 — year-omitted date vs multi-year deadlines (무연도 날짜 오매칭)
# ---------------------------------------------------------------------------

_M5_SOURCE = "1차 접수는 2025년 3월 15일까지이고, 2차 접수는 2026년 3월 15일까지입니다."


def test_m5_yearless_easy_date_must_not_cover_two_years():
    # 연도가 생략된 '3월 15일까지'가 2025/2026 두 마감일 모두에 매칭돼
    # 하나가 통째로 누락됐는데 PASS 되면 안 된다.
    report = verify(_doc(_M5_SOURCE), "접수는 3월 15일까지입니다.", REF)
    assert report.verdict != Verdict.PASS


def test_m5_both_years_explicit_passes():
    easy = "1차 접수는 2025년 3월 15일까지, 2차 접수는 2026년 3월 15일까지입니다."
    report = verify(_doc(_M5_SOURCE), easy, REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


def test_m5_single_deadline_yearless_easy_still_ok():
    # 원문 연도가 하나뿐이면 무연도 표현은 기존대로 그 연도로 해석돼 PASS.
    src = "건강보험료를 2026년 7월 17일까지 납부하세요."
    report = verify(_doc(src), "보험료를 7월 17일까지 내세요.", REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


# ---------------------------------------------------------------------------
# M6 — double-negation polarity reversal (이중부정 극성 반전)
# ---------------------------------------------------------------------------

_M6_SOURCE = "전과 기록이 있는 자는 지원 대상에서 제외됩니다."


def test_m6_double_negation_reversal_is_human_review():
    # 부정 마커('제외')가 표면상 보존됐지만 곧바로 재부정되어 의미가 반전된 경우.
    easy = ("전과 기록이 있으면 원래 지원 대상에서 제외됩니다 라고 생각하기 쉽지만, "
            "실제로는 그렇지 않으며 누구나 지원할 수 있습니다.")
    report = verify(_doc(_M6_SOURCE), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m6_negated_marker_suffix_is_human_review():
    # '제외되지 않고' — 마커 직후 '~지 않' 재부정.
    easy = "전과 기록이 있어도 지원 대상에서 제외되지 않고 신청할 수 있습니다."
    report = verify(_doc(_M6_SOURCE), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m6_faithful_negation_control_passes():
    easy = "전과 기록이 있는 사람은 지원 대상에서 제외됩니다."
    report = verify(_doc(_M6_SOURCE), easy, REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


# ---------------------------------------------------------------------------
# M7 — empty source must never auto-PASS a non-empty easy text
# ---------------------------------------------------------------------------


def test_m7_empty_source_nonempty_easy_is_human_review():
    empty = Document(blocks=[], source_mime="text/plain")
    fabricated = "신청 기한은 2099년 12월 31일까지입니다. 누구나 지원금을 받을 수 있습니다."
    report = verify(empty, fabricated, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


# ---------------------------------------------------------------------------
# M8 — agency swap (기관명 바꿔치기)
#   기관명은 자동교정이 불가능한 의미 슬롯(router: not AUTO_RECOVERABLE)이므로
#   원문 기관명이 쉬운본에서 사라지면 HUMAN_REVIEW로 가야 한다.
# ---------------------------------------------------------------------------

_M8_SOURCE = "임대차 계약 신고는 강서구청 민원실에 하시기 바랍니다."


def test_m8_agency_swap_is_human_review():
    # 강서구청 -> 송파구청: 접수처 바꿔치기. 잘못된 기관으로 안내되면
    # 이용자가 실제 불이익을 받으므로 절대 PASS 되면 안 된다.
    report = verify(_doc(_M8_SOURCE), "임대차 계약 신고는 송파구청 민원실에 하세요.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW
    assert any(s.type == SlotType.AGENCY for s in report.failed_slots)


def test_m8_agency_dropped_not_pass():
    report = verify(_doc(_M8_SOURCE), "임대차 계약 신고는 민원실에 하세요.", REF)
    assert report.verdict != Verdict.PASS


def test_m8_faithful_agency_control_passes():
    report = verify(_doc(_M8_SOURCE), "임대차 계약 신고는 강서구청 민원실에 하세요.", REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


def test_m8_public_corporation_swap_is_human_review():
    src = "연금은 국민연금공단에서 지급합니다."
    report = verify(_doc(src), "연금은 근로복지공단에서 지급합니다.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m8_agency_spacing_variant_passes():
    # Easy-Read는 복합어 띄어쓰기를 권장한다 — '강서 구청'은 왜곡이 아니다.
    # (공백 민감 비교면 무손상 쉬운본이 HUMAN_REVIEW로 종료되는 거짓 양성)
    report = verify(_doc(_M8_SOURCE), "임대차 계약 신고는 강서 구청 민원실에 하세요.", REF)
    assert report.verdict == Verdict.PASS, report.failed_slots


def test_m8_agency_swap_with_spacing_still_human_review():
    # 띄어쓰기 관용이 바꿔치기 탐지를 무르게 하면 안 된다.
    report = verify(_doc(_M8_SOURCE), "임대차 계약 신고는 송파 구청 민원실에 하세요.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


# ---------------------------------------------------------------------------
# M9 — bare count distortion (단위명사 붙은 일반 숫자 왜곡)
#   금액/날짜 형식이 아닌 '개수'(명/건/가구/% 등)는 기존 게이트의 사각지대였다.
#   왜곡은 REVISE(자동 재교정 가능), 표기 변형(콤마·퍼센트·고유어 수사)은 PASS.
# ---------------------------------------------------------------------------

_M9_SOURCE = "올해 지원 대상자는 총 300명입니다."


def test_m9_count_distortion_not_pass():
    # 300명 -> 3,000명: 자릿수 왜곡이 PASS로 통과되면 안 된다.
    report = verify(_doc(_M9_SOURCE), "올해 지원 대상자는 총 3,000명입니다.", REF)
    assert report.verdict == Verdict.REVISE
    assert any(s.type == SlotType.NUMERIC for s in report.failed_slots)


def test_m9_faithful_count_control_passes():
    report = verify(_doc(_M9_SOURCE), "올해 지원 대상자는 모두 300명이에요.", REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


def test_m9_count_no_tail_substring_survival():
    # '5,000명'이 '15,000명'의 꼬리로 생존 처리되면 안 된다 (M3와 동일 원칙).
    src = "행사 정원은 5,000명입니다."
    report = verify(_doc(src), "행사 정원은 15,000명입니다.", REF)
    assert report.verdict != Verdict.PASS


def test_m9_percent_surface_variants_pass():
    # 퍼센트 <-> % 표기 차이는 같은 값이다.
    src = "기준 중위소득의 32퍼센트가 기준입니다."
    report = verify(_doc(src), "기준 중위소득의 32%가 기준이에요.", REF)
    assert report.verdict == Verdict.PASS, report.drift_flags


def test_m9_native_numeral_rephrase_passes():
    # 쉬운 글은 '1명당'을 '한 명마다'로 풀어 쓴다 — 고유어 수사는 같은 값.
    src = "아동 1명당 100,000원을 지급합니다."
    report = verify(_doc(src), "아동 한 명마다 100,000원을 드려요.", REF)
    assert report.verdict == Verdict.PASS, report.drift_flags
