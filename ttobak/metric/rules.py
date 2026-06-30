"""Rule-based K-ER rubric — twelve rule functions and ALL_RULES registry.

Each rule function accepts (text: str, tokens: list[Token]) and returns a
RuleResult with a sub_score (0-100, higher = easier) and a list of Violations.
Rules are deterministic given an injected token list; kiwipiepy is NOT imported here.

Spec references:
  §5.1 Rule table (threshold documentation per rule)
  §5.2(1) Scoring formula — mean of sub_scores
  §5.3 Level estimate mapping (score ≥80 → 1, ≥60 → 2, else → 3)
"""
from __future__ import annotations

import importlib.resources
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel

from ttobak.common import Severity
from ttobak.metric.models import Violation
from ttobak.metric.tokenize import Token

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class RuleResult(BaseModel):
    sub_score: float
    violations: list[Violation]


# ---------------------------------------------------------------------------
# Seed-list loader (importlib.resources — works when installed as a package)
# ---------------------------------------------------------------------------

def _load_list(filename: str) -> frozenset[str]:
    """Load a seed word list from ttobak/data/*.txt, ignoring comment lines."""
    try:
        # Python 3.9+ importlib.resources.files API
        ref = importlib.resources.files("ttobak.data").joinpath(filename)
        text = ref.read_text(encoding="utf-8")
    except Exception:
        # Fallback: resolve relative to this file
        base = Path(__file__).parent.parent / "data" / filename
        text = base.read_text(encoding="utf-8")

    words: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.add(line)
    return frozenset(words)


_EASY_WORDS: frozenset[str] = frozenset()
_HARD_TERMS: frozenset[str] = frozenset()
_IDIOMS: frozenset[str] = frozenset()


def _ensure_loaded() -> None:
    global _EASY_WORDS, _HARD_TERMS, _IDIOMS
    if not _EASY_WORDS:
        _EASY_WORDS = _load_list("easy_words.txt")
    if not _HARD_TERMS:
        _HARD_TERMS = _load_list("hard_terms.txt")
    if not _IDIOMS:
        _IDIOMS = _load_list("idioms.txt")


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(
    r"[一-鿿㐀-䶿豈-﫿"
    r"⺀-⻿⼀-⿟]"
)
_LATIN_RE = re.compile(r"[A-Za-z]")
_ABBREV_RE = re.compile(r"\b[A-Z]{2,}\b")
_PERCENT_RE = re.compile(r"\d+\s*%")
_BIGNUM_RE = re.compile(r"\d[\d,]{5,}")  # ≥6 digits (i.e. ≥100,000)
_NEG_LEXEMES = frozenset(["안", "못", "없", "말", "아니", "불가", "금지", "제외"])
_PASSIVE_FORMS = frozenset(["되", "지다", "받다", "당하다"])
_3RD_PERSON = frozenset(["그", "그녀"])
_DIRECT_ADDRESS = frozenset(["당신", "여러분", "우리"])
_CONNECTIVE_TAGS = frozenset(["EC"])
_MODIFIER_TAGS = frozenset(["MM", "MAG"])
_NNG_TAGS = frozenset(["NNG", "NNP", "NNB", "NR", "NP"])
_VERB_TAGS = frozenset(["VV", "VA", "XSV"])


def _noun_tokens(tokens: list[Token]) -> list[Token]:
    return [t for t in tokens if t.tag in _NNG_TAGS]


def _content_tokens(tokens: list[Token]) -> list[Token]:
    """Content morphemes: nouns + verbs + adjectives."""
    return [t for t in tokens if t.tag[:2] in {"NN", "VV", "VA", "XS"}]


# ---------------------------------------------------------------------------
# Rule 1: sentence_length  (spec §5.1 R-01)
#
# Threshold: sentences ≤15 tokens → full score (100).
# Score degrades linearly from 15 to 40 tokens; >40 → 0.
# Violation: MED when a sentence exceeds 15 tokens.
# ---------------------------------------------------------------------------

_SENT_SPLIT_RE = re.compile(r"(?<=[.!?。])\s+|\n+")
_SL_EASY = 15   # tokens per sentence — spec §5.1 R-01
_SL_HARD = 40


def _sent_tokens(text: str, tokens: list[Token]) -> list[int]:
    """Return token count per sentence (proxy: split text + proportion)."""
    sents = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    n = len(sents)
    if n == 0:
        return [len(tokens)]
    # Distribute tokens proportionally by character count
    char_counts = [len(s) for s in sents]
    total_chars = sum(char_counts)
    if total_chars == 0:
        return [len(tokens)] * n
    counts = []
    distributed = 0
    total_toks = len(tokens)
    for i, cc in enumerate(char_counts):
        if i == n - 1:
            counts.append(total_toks - distributed)
        else:
            c = round(total_toks * cc / total_chars)
            counts.append(c)
            distributed += c
    return counts


def rule_sentence_length(text: str, tokens: list[Token]) -> RuleResult:
    """R-01: Sentence length ≤15 tokens → 100; >40 → 0. (spec §5.1 R-01)"""
    sents = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    if not sents:
        sents = [text.strip()]
    tok_counts = _sent_tokens(text, tokens)
    violations: list[Violation] = []
    scores: list[float] = []
    for sent, cnt in zip(sents, tok_counts):
        if cnt <= _SL_EASY:
            scores.append(100.0)
        elif cnt >= _SL_HARD:
            scores.append(0.0)
            violations.append(Violation(
                rule="sentence_length",
                span=sent[:60],
                severity=Severity.HIGH,
                suggestion=f"문장이 너무 깁니다({cnt}개 형태소). 두 문장으로 나누세요.",
            ))
        else:
            ratio = (cnt - _SL_EASY) / (_SL_HARD - _SL_EASY)
            sc = 100.0 * (1.0 - ratio)
            scores.append(sc)
            violations.append(Violation(
                rule="sentence_length",
                span=sent[:60],
                severity=Severity.MED,
                suggestion=f"문장이 길어요({cnt}개 형태소). 짧게 나누면 더 읽기 쉬워요.",
            ))
    sub_score = sum(scores) / len(scores) if scores else 100.0
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 2: hard_word_ratio  (spec §5.1 R-02)
#
# Among NNG tokens: ratio not in easy_words list → penalise.
# 0% hard → 100; ≥50% hard → 0.
# ---------------------------------------------------------------------------

def rule_hard_word_ratio(text: str, tokens: list[Token]) -> RuleResult:
    """R-02: High proportion of non-easy nouns lowers score. (spec §5.1 R-02)"""
    _ensure_loaded()
    nouns = _noun_tokens(tokens)
    if not nouns:
        return RuleResult(sub_score=100.0, violations=[])
    hard = [t for t in nouns if t.form not in _EASY_WORDS]
    ratio = len(hard) / len(nouns)
    sub_score = max(0.0, 100.0 - ratio * 200.0)  # 50% hard → 0
    violations: list[Violation] = []
    if ratio >= 0.3:
        sample = ", ".join(t.form for t in hard[:5])
        violations.append(Violation(
            rule="hard_word_ratio",
            span=sample,
            severity=Severity.MED,
            suggestion="어려운 낱말을 쉬운 말로 바꾸거나 괄호 안에 설명을 달아 주세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 3: hanja_loanword_ratio  (spec §5.1 R-03)
#
# CJK codepoints in NNG surface forms + Latin sequences as proxy for
# Sino-Korean / loanword density. ≥50% → 0; 0% → 100.
# ---------------------------------------------------------------------------

def rule_hanja_loanword_ratio(text: str, tokens: list[Token]) -> RuleResult:
    """R-03: Sino-Korean / loanword density (CJK + Latin). (spec §5.1 R-03)"""
    nouns = _noun_tokens(tokens)
    if not nouns:
        return RuleResult(sub_score=100.0, violations=[])
    flagged = [
        t for t in nouns
        if _CJK_RE.search(t.form) or _LATIN_RE.search(t.form)
    ]
    ratio = len(flagged) / len(nouns)
    sub_score = max(0.0, 100.0 - ratio * 200.0)
    violations: list[Violation] = []
    if ratio >= 0.4:
        sample = ", ".join(t.form for t in flagged[:5])
        violations.append(Violation(
            rule="hanja_loanword_ratio",
            span=sample,
            severity=Severity.MED,
            suggestion="한자어나 외래어를 쉬운 우리말로 바꿔 주세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 4: predicates_connectives  (spec §5.1 R-04)
#
# Many connective endings (EC) per sentence → complex clause chaining.
# ≤1 EC per sentence → 100; ≥4 → 0.
# ---------------------------------------------------------------------------

def rule_predicates_connectives(text: str, tokens: list[Token]) -> RuleResult:
    """R-04: Connective-endings (EC) density. (spec §5.1 R-04)"""
    sents = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    if not sents:
        sents = [text]
    tok_counts = _sent_tokens(text, tokens)
    ec_tokens = [t for t in tokens if t.tag in _CONNECTIVE_TAGS]
    n_ec = len(ec_tokens)
    n_sents = max(1, len(sents))
    ec_per_sent = n_ec / n_sents

    _EASY_EC = 1.0
    _HARD_EC = 4.0
    if ec_per_sent <= _EASY_EC:
        sub_score = 100.0
    elif ec_per_sent >= _HARD_EC:
        sub_score = 0.0
    else:
        sub_score = 100.0 * (1.0 - (ec_per_sent - _EASY_EC) / (_HARD_EC - _EASY_EC))

    violations: list[Violation] = []
    if ec_per_sent > _EASY_EC:
        violations.append(Violation(
            rule="predicates_connectives",
            span=text[:60],
            severity=Severity.MED,
            suggestion="접속 어미(~고, ~어서, ~지만 등)를 줄이고 문장을 나눠 주세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 5: passive_ratio  (spec §5.1 R-05)
#
# XSV 되 or 지다/받다/당하다 following NNG/NNP → passive construction.
# >30% of verbs passive → penalise.
# ---------------------------------------------------------------------------

def rule_passive_ratio(text: str, tokens: list[Token]) -> RuleResult:
    """R-05: Passive constructions ratio. (spec §5.1 R-05)"""
    verbs = [t for t in tokens if t.tag in _VERB_TAGS]
    if not verbs:
        return RuleResult(sub_score=100.0, violations=[])

    passive_hits: list[Token] = []
    for i, t in enumerate(tokens):
        if t.form in _PASSIVE_FORMS and t.tag in {"XSV", "VV"}:
            # attach preceding noun as span if available
            passive_hits.append(t)

    ratio = len(passive_hits) / len(verbs)
    _EASY_P = 0.1
    _HARD_P = 0.5
    if ratio <= _EASY_P:
        sub_score = 100.0
    elif ratio >= _HARD_P:
        sub_score = 0.0
    else:
        sub_score = 100.0 * (1.0 - (ratio - _EASY_P) / (_HARD_P - _EASY_P))

    violations: list[Violation] = []
    if passive_hits:
        # Build span from surrounding context
        prev_nouns = [tokens[i - 1].form for i, t in enumerate(tokens)
                      if t in passive_hits and i > 0 and tokens[i - 1].tag in _NNG_TAGS]
        span = ", ".join(prev_nouns[:3]) if prev_nouns else passive_hits[0].form
        violations.append(Violation(
            rule="passive_ratio",
            span=span,
            severity=Severity.MED,
            suggestion="피동 표현을 능동 표현으로 바꾸세요. 예: '처리됩니다' → '처리합니다'.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 6: negation_ratio  (spec §5.1 R-06)
#
# Negation lexemes (안/못/없/말/아니/불가/금지/제외) in token surface.
# >1 negation per sentence → flag.
# ---------------------------------------------------------------------------

def rule_negation_ratio(text: str, tokens: list[Token]) -> RuleResult:
    """R-06: Negation density. (spec §5.1 R-06)"""
    neg_hits = [t for t in tokens if t.form in _NEG_LEXEMES]
    sents = [s for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    n_sents = max(1, len(sents))
    neg_per_sent = len(neg_hits) / n_sents

    _EASY_N = 0.5
    _HARD_N = 2.0
    if neg_per_sent <= _EASY_N:
        sub_score = 100.0
    elif neg_per_sent >= _HARD_N:
        sub_score = 0.0
    else:
        sub_score = 100.0 * (1.0 - (neg_per_sent - _EASY_N) / (_HARD_N - _EASY_N))

    violations: list[Violation] = []
    if neg_hits:
        sample = ", ".join(t.form for t in neg_hits[:3])
        violations.append(Violation(
            rule="negation_ratio",
            span=sample,
            severity=Severity.MED,
            suggestion="부정 표현을 긍정 표현으로 바꿔 주세요. 예: '~할 수 없습니다' → '~하지 못합니다' 혹은 긍정 재술.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 7: undefined_hard_term  (spec §5.1 R-07)
#
# Hard-term tokens (from hard_terms.txt) without corresponding easy word
# replacement or parenthetical explanation.
# ---------------------------------------------------------------------------

_PAREN_RE = re.compile(r"\(([^)]+)\)")


def rule_undefined_hard_term(text: str, tokens: list[Token]) -> RuleResult:
    """R-07: Hard specialist terms without explanation. (spec §5.1 R-07)"""
    _ensure_loaded()
    # Extract parenthetical definitions already present
    defined = set()
    for m in _PAREN_RE.finditer(text):
        defined.add(m.group(1).strip())

    hard_hits = [t for t in tokens if t.form in _HARD_TERMS and t.form not in defined]
    n_nouns = max(1, len(_noun_tokens(tokens)))
    ratio = len(hard_hits) / n_nouns

    _EASY_H = 0.0
    _HARD_H = 0.3
    if ratio <= _EASY_H:
        sub_score = 100.0
    elif ratio >= _HARD_H:
        sub_score = 0.0
    else:
        sub_score = 100.0 * (1.0 - ratio / _HARD_H)

    violations: list[Violation] = []
    if hard_hits:
        sample = ", ".join(t.form for t in hard_hits[:5])
        violations.append(Violation(
            rule="undefined_hard_term",
            span=sample,
            severity=Severity.HIGH,
            suggestion="전문 용어를 괄호 안에 쉬운 말로 설명하거나 바꿔 주세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 8: idiom  (spec §5.1 R-08)
#
# Idiom / figurative expression from idioms.txt found in text.
# Any idiom → sub_score penalty; each idiom = 20 points off.
# ---------------------------------------------------------------------------

def rule_idiom(text: str, tokens: list[Token]) -> RuleResult:
    """R-08: Idiomatic / figurative expressions. (spec §5.1 R-08)"""
    _ensure_loaded()
    hits = [idiom for idiom in _IDIOMS if idiom in text]
    penalty = min(len(hits) * 20.0, 100.0)
    sub_score = max(0.0, 100.0 - penalty)
    violations: list[Violation] = []
    for idiom in hits[:5]:
        violations.append(Violation(
            rule="idiom",
            span=idiom,
            severity=Severity.MED,
            suggestion=f"관용 표현 '{idiom}'을 쉬운 말로 풀어서 쓰세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 9: abbrev_percent_bignum  (spec §5.1 R-09)
#
# Abbreviations (≥2 uppercase Latin letters), % notation without definition,
# or very large numbers (≥6 digits) without explanation.
# Each occurrence → 10-point penalty.
# ---------------------------------------------------------------------------

def rule_abbrev_percent_bignum(text: str, tokens: list[Token]) -> RuleResult:
    """R-09: Abbreviations, %, and large numbers without explanation. (§5.1 R-09)"""
    abbrevs = _ABBREV_RE.findall(text)
    percents = _PERCENT_RE.findall(text)
    bignums = _BIGNUM_RE.findall(text)

    all_hits = abbrevs + percents + bignums
    penalty = min(len(all_hits) * 10.0, 100.0)
    sub_score = max(0.0, 100.0 - penalty)

    violations: list[Violation] = []
    for h in all_hits[:5]:
        violations.append(Violation(
            rule="abbrev_percent_bignum",
            span=h,
            severity=Severity.MED,
            suggestion="약어·퍼센트·큰 숫자는 쉽게 풀어서 설명해 주세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 10: third_person_fictional  (spec §5.1 R-10)
#
# Pronoun 그/그녀 or fictional persona patterns → abstract distance.
# Any presence → penalty.
# ---------------------------------------------------------------------------

def rule_third_person_fictional(text: str, tokens: list[Token]) -> RuleResult:
    """R-10: Third-person fictional pronouns (그/그녀). (spec §5.1 R-10)"""
    hits = [t for t in tokens if t.form in _3RD_PERSON and t.tag in {"NP", "NNG"}]
    penalty = min(len(hits) * 15.0, 60.0)
    sub_score = max(40.0, 100.0 - penalty)

    violations: list[Violation] = []
    if hits:
        sample = ", ".join(t.form for t in hits[:3])
        violations.append(Violation(
            rule="third_person_fictional",
            span=sample,
            severity=Severity.LOW,
            suggestion="'그'/'그녀' 대신 직접 호칭(예: '신청인')을 쓰세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 11: direct_address  (spec §5.1 R-11)
#
# Presence of 당신/여러분/우리 → rewards reader-direct register.
# Absence from text → small score reduction.
# ---------------------------------------------------------------------------

def rule_direct_address(text: str, tokens: list[Token]) -> RuleResult:
    """R-11: Direct-address register (당신/여러분/우리). (spec §5.1 R-11)"""
    hits = [t for t in tokens if t.form in _DIRECT_ADDRESS]
    # Reward presence (these improve accessibility)
    sub_score = 70.0 + min(len(hits) * 10.0, 30.0)
    violations: list[Violation] = []
    if not hits:
        violations.append(Violation(
            rule="direct_address",
            span="(없음)",
            severity=Severity.LOW,
            suggestion="'여러분', '당신' 등 독자를 직접 부르는 표현을 사용해 친근감을 높이세요.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# Rule 12: modifier_ttr  (spec §5.1 R-12)
#
# Type-token ratio (TTR) of modifier tokens (MM/MAG).
# Low TTR (few distinct modifier forms) → moderate register; high TTR → complex.
# TTR ≤0.4 → 100; TTR ≥0.9 → 40; linearly interpolated.
# ---------------------------------------------------------------------------

def rule_modifier_ttr(text: str, tokens: list[Token]) -> RuleResult:
    """R-12: Modifier type-token ratio (MM/MAG TTR). (spec §5.1 R-12)"""
    mods = [t for t in tokens if t.tag in _MODIFIER_TAGS]
    if not mods:
        return RuleResult(sub_score=80.0, violations=[])  # neutral when absent

    ttr = len({t.form for t in mods}) / len(mods)
    _EASY_TTR = 0.4
    _HARD_TTR = 0.9
    if ttr <= _EASY_TTR:
        sub_score = 100.0
    elif ttr >= _HARD_TTR:
        sub_score = 40.0
    else:
        ratio = (ttr - _EASY_TTR) / (_HARD_TTR - _EASY_TTR)
        sub_score = 100.0 - ratio * 60.0

    violations: list[Violation] = []
    if ttr > 0.7:
        violations.append(Violation(
            rule="modifier_ttr",
            span=text[:60],
            severity=Severity.LOW,
            suggestion="수식어(관형사·부사)가 다양합니다. 단순하고 반복적인 표현이 이해하기 쉽습니다.",
        ))
    return RuleResult(sub_score=sub_score, violations=violations)


# ---------------------------------------------------------------------------
# ALL_RULES registry — ordered list of (name, callable) pairs
# ---------------------------------------------------------------------------

ALL_RULES: list[tuple[str, callable]] = [
    ("sentence_length",       rule_sentence_length),
    ("hard_word_ratio",       rule_hard_word_ratio),
    ("hanja_loanword_ratio",  rule_hanja_loanword_ratio),
    ("predicates_connectives", rule_predicates_connectives),
    ("passive_ratio",          rule_passive_ratio),
    ("negation_ratio",         rule_negation_ratio),
    ("undefined_hard_term",    rule_undefined_hard_term),
    ("idiom",                  rule_idiom),
    ("abbrev_percent_bignum",  rule_abbrev_percent_bignum),
    ("third_person_fictional", rule_third_person_fictional),
    ("direct_address",         rule_direct_address),
    ("modifier_ttr",           rule_modifier_ttr),
]
