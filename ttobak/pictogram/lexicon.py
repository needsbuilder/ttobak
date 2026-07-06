from __future__ import annotations

from ttobak.pictogram.models import PictogramRef

# Hand-curated ~30 high-frequency Korean public/admin concepts -> real glyph
# path refs. Assets live in /assets/pictograms/<set>/ under their own CC BY-SA
# license; here we only carry path refs + Korean captions (spec 9.4).
#
# Set assignment note (verified 2026-07-06 against the real asset libraries):
# Mulberry Symbols is an AAC/communication-board vocabulary (concrete, everyday
# concepts) and has no usable symbol for abstract admin/legal concepts like tax,
# insurance, deadline, application, benefit, bank account, address, or mail as a
# noun (checked its 3436-symbol index). Those concepts use OpenMoji instead —
# already the project's documented secondary set for exactly this gap (spec
# 9.4) — rather than force a poor-fit Mulberry symbol. See
# assets/pictograms/openmoji/ATTRIBUTION.md for the full reasoning + mapping.
#
# Financial-cluster distinctness (fixed after adversarial review 2026-07-06):
# 돈/금액, 계좌, 은행 must render as VISUALLY DISTINCT glyphs (a low-literacy
# reader relies on the picture, not the caption). 돈/금액 = OpenMoji money bag,
# 계좌 = OpenMoji ledger (통장), 은행 = Mulberry bank building. (Earlier all three
# collapsed to the same bank-building glyph — money.svg was a byte-identical copy
# of bank.svg — which defeated the whole point of the pictograms.)
_RAW: dict[str, tuple[str, str, str]] = {
    "돈": ("openmoji", "openmoji/money.svg", "돈"),
    "금액": ("openmoji", "openmoji/money.svg", "돈"),
    "납부": ("openmoji", "openmoji/pay.svg", "돈을 내요"),
    "세금": ("openmoji", "openmoji/tax.svg", "세금"),
    "날짜": ("openmoji", "openmoji/calendar.svg", "날짜"),
    "기한": ("openmoji", "openmoji/calendar.svg", "날짜"),
    "마감": ("openmoji", "openmoji/deadline.svg", "마감 날짜"),
    "신청": ("openmoji", "openmoji/apply.svg", "신청"),
    "접수": ("openmoji", "openmoji/apply.svg", "신청"),
    "서류": ("mulberry", "mulberry/document.svg", "서류"),
    "전화": ("mulberry", "mulberry/phone.svg", "전화"),
    "연락": ("mulberry", "mulberry/phone.svg", "전화"),
    "주소": ("openmoji", "openmoji/address.svg", "주소"),
    "방문": ("mulberry", "mulberry/visit.svg", "찾아가요"),
    "병원": ("mulberry", "mulberry/hospital.svg", "병원"),
    "약": ("mulberry", "mulberry/medicine.svg", "약"),
    "건강": ("openmoji", "openmoji/health.svg", "건강"),
    "보험": ("openmoji", "openmoji/insurance.svg", "보험"),
    "은행": ("mulberry", "mulberry/bank.svg", "은행"),
    "계좌": ("openmoji", "openmoji/bank_account.svg", "은행 계좌"),
    "주민센터": ("mulberry", "mulberry/office.svg", "주민센터"),
    "구청": ("mulberry", "mulberry/office.svg", "구청"),
    "우편": ("openmoji", "openmoji/mail.svg", "우편"),
    "이메일": ("openmoji", "openmoji/email.svg", "이메일"),
    "홈페이지": ("openmoji", "openmoji/website.svg", "홈페이지"),
    "지원": ("openmoji", "openmoji/support.svg", "도와줘요"),
    "혜택": ("openmoji", "openmoji/benefit.svg", "혜택"),
    "자격": ("mulberry", "mulberry/eligible.svg", "받을 수 있어요"),
    "주의": ("openmoji", "openmoji/warning.svg", "조심하세요"),
    "금지": ("openmoji", "openmoji/forbidden.svg", "하면 안 돼요"),
    "시간": ("mulberry", "mulberry/clock.svg", "시간"),
    "장소": ("openmoji", "openmoji/place.svg", "장소"),
}

LEXICON: dict[str, PictogramRef] = {
    keyword: PictogramRef(concept=keyword, set=set_name, glyph_id=glyph_id, caption=caption)
    for keyword, (set_name, glyph_id, caption) in _RAW.items()
}

# 1-syllable keyword false-positive guard (bug fix, verified via reproduction):
# substring matching on a single Hangul syllable also fires inside unrelated
# compound words where that syllable is a bound morpheme, not the standalone
# concept ("약" = medicine matches "계약"=contract, "요약"=summary, etc.).
# match() consults this per-keyword stoplist of 2-syllable windows before
# accepting an occurrence, and keeps scanning past a stoplisted occurrence for
# a legitimate one. Only keywords with a confirmed false-positive get an
# entry here; other 1-syllable keywords are unaffected.
FALSE_POSITIVE_COMPOUNDS: dict[str, frozenset[str]] = {
    "약": frozenset(
        {
            "계약", "예약", "요약", "절약",  # 약 as the 2nd syllable
            "약간", "약속", "약관",  # 약 as the 1st syllable
            "규약", "공약", "조약",  # 약 as the 2nd syllable
        }
    ),
}
