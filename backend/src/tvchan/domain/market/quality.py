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
        if not isinstance(self.kind, BarMutationKind):
            raise TypeError("kind must be BarMutationKind")
        if not isinstance(self.identity, tuple) or len(self.identity) != 4:
            raise TypeError("identity must be a BarIdentity tuple")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must not be empty")


@dataclass(frozen=True, slots=True)
class QualityReport:
    quality: QualityStatus
    completeness: CompletenessStatus
    mutations: tuple[BarMutation, ...] = ()
    messages: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.quality, QualityStatus):
            raise TypeError("quality must be QualityStatus")
        if not isinstance(self.completeness, CompletenessStatus):
            raise TypeError("completeness must be CompletenessStatus")
        if not isinstance(self.mutations, tuple):
            raise TypeError("mutations must be a tuple")
        if not all(isinstance(mutation, BarMutation) for mutation in self.mutations):
            raise TypeError("mutations must contain BarMutation values")
        if not isinstance(self.messages, tuple):
            raise TypeError("messages must be a tuple")
        if not all(isinstance(message, str) and message.strip() for message in self.messages):
            raise ValueError("messages must contain non-empty strings")
