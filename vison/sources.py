"""Opportunity sources. Sample data is only for local MVP demonstrations."""

from __future__ import annotations

from datetime import date

from .models import Opportunity


def sample_opportunities() -> list[Opportunity]:
    """Return transparent local fixtures; these are not live listings."""
    return [
        Opportunity(
            title="Open Innovation Build Weekend",
            organizer="Vison demo partner",
            opportunity_type="hackathon",
            location="Remote",
            remote=True,
            deadline=date(2026, 11, 15),
            source_url="https://example.com/vison-demo-hackathon",
            interests=("ai", "climate", "web"),
            skills=("python", "javascript", "design"),
            experience_levels=("beginner", "student", "early-career"),
            eligibility_note="Demo fixture: verify all eligibility details with an official organizer before applying.",
        ),
        Opportunity(
            title="Data for Good Internship",
            organizer="Vison demo partner",
            opportunity_type="internship",
            location="Bengaluru, India",
            remote=False,
            deadline=date(2026, 12, 1),
            source_url="https://example.com/vison-demo-internship",
            interests=("ai", "data", "social impact"),
            skills=("python", "sql", "machine learning"),
            experience_levels=("student", "early-career"),
            eligibility_note="Demo fixture: location and work-authorisation requirements are unverified.",
        ),
        Opportunity(
            title="Open Source Accessibility Sprint",
            organizer="Vison demo partner",
            opportunity_type="hackathon",
            location="Remote",
            remote=True,
            deadline=None,
            source_url="https://example.com/vison-demo-accessibility",
            interests=("accessibility", "web", "open source"),
            skills=("javascript", "python", "ux"),
            experience_levels=(),
            eligibility_note=None,
        ),
    ]

