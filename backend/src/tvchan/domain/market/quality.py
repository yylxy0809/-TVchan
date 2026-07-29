"""Immutable quality and completeness result vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from tvchan.domain.market.model import BarIdentity


class QualityStatus(StrEnum):
    VALIDATED = "VALIDATED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"


class CompletenessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class BarMutationKind(StrEnum):
    REPAIRED = "REPAIRED"
    DROPPED = "DROPPED"


@dataclass(frozen=True, slots=True)
class BarMutation:
    kind: BarMutationKind
    identity: BarIdentity
    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class QualityReport:
    quality: QualityStatus
    completeness: CompletenessStatus
    mutations: tuple[BarMutation, ...] = ()
    messages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(message for message in self.messages):
            raise ValueError("messages must not contain empty strings")
