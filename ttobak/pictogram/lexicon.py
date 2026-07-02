from __future__ import annotations

from ttobak.pictogram.models import PictogramRef

# Hand-curated ~30 high-frequency Korean public/admin concepts -> placeholder
# glyph path refs. Assets live in /assets/pictograms/<set>/ under their own
# CC BY-SA license; here we only carry path refs + Korean captions (spec 9.4).
_RAW: dict[str, tuple[str, str, str]] = {
    "돈": ("mulberry", "mulberry/money.svg", "돈"),
    "금액": ("mulberry", "mulberry/money.svg", "돈"),
    "납부": ("mulberry", "mulberry/pay.svg", "돈을 내요"),
    "세금": ("mulberry", "mulberry/tax.svg", "세금"),
    "날짜": ("mulberry", "mulberry/calendar.svg", "날짜"),
    "기한": ("mulberry", "mulberry/calendar.svg", "날짜"),
    "마감": ("mulberry", "mulberry/deadline.svg", "마감 날짜"),
    "신청": ("mulberry", "mulberry/apply.svg", "신청"),
    "접수": ("mulberry", "mulberry/apply.svg", "신청"),
    "서류": ("mulberry", "mulberry/document.svg", "서류"),
    "전화": ("mulberry", "mulberry/phone.svg", "전화"),
    "연락": ("mulberry", "mulberry/phone.svg", "전화"),
    "주소": ("mulberry", "mulberry/address.svg", "주소"),
    "방문": ("mulberry", "mulberry/visit.svg", "찾아가요"),
    "병원": ("mulberry", "mulberry/hospital.svg", "병원"),
    "약": ("mulberry", "mulberry/medicine.svg", "약"),
    "건강": ("mulberry", "mulberry/health.svg", "건강"),
    "보험": ("mulberry", "mulberry/insurance.svg", "보험"),
    "은행": ("mulberry", "mulberry/bank.svg", "은행"),
    "계좌": ("mulberry", "mulberry/bank_account.svg", "은행 계좌"),
    "주민센터": ("mulberry", "mulberry/office.svg", "주민센터"),
    "구청": ("mulberry", "mulberry/office.svg", "구청"),
    "우편": ("mulberry", "mulberry/mail.svg", "우편"),
    "이메일": ("openmoji", "openmoji/email.svg", "이메일"),
    "홈페이지": ("openmoji", "openmoji/website.svg", "홈페이지"),
    "지원": ("mulberry", "mulberry/support.svg", "도와줘요"),
    "혜택": ("mulberry", "mulberry/benefit.svg", "혜택"),
    "자격": ("mulberry", "mulberry/eligible.svg", "받을 수 있어요"),
    "주의": ("openmoji", "openmoji/warning.svg", "조심하세요"),
    "금지": ("openmoji", "openmoji/forbidden.svg", "하면 안 돼요"),
    "시간": ("mulberry", "mulberry/clock.svg", "시간"),
    "장소": ("mulberry", "mulberry/place.svg", "장소"),
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
