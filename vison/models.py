"""Small, explicit data models used by the local Vison MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal


OpportunityType = Literal["hackathon", "internship"]


@dataclass(frozen=True)
class UserProfile:
    interests: tuple[str, ...]
    skills: tuple[str, ...]
    location: str
    remote_ok: bool
    experience_level: str
    opportunity_types: tuple[OpportunityType, ...]


@dataclass(frozen=True)
class Opportunity:
    title: str
    organizer: str
    opportunity_type: OpportunityType
    location: str
    remote: bool
    deadline: date | None
    source_url: str
    interests: tuple[str, ...] = field(default_factory=tuple)
    skills: tuple[str, ...] = field(default_factory=tuple)
    experience_levels: tuple[str, ...] = field(default_factory=tuple)
    eligibility_note: str | None = None
    source_label: str = "sample data"


@dataclass(frozen=True)
class MatchResult:
    opportunity: Opportunity
    score: int
    reasons: tuple[str, ...]
    uncertainties: tuple[str, ...]

