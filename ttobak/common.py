"""Shared cross-module enums (canonical contracts).

Every module MUST import Severity / Verdict from here and MUST NOT redefine them.
"""

from enum import Enum


class Severity(str, Enum):
    HIGH = "high"
    MED = "med"
    LOW = "low"


class Verdict(str, Enum):
    PASS = "pass"
    REVISE = "revise"
    HUMAN_REVIEW = "human_review"
