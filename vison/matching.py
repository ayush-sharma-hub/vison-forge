"""Explainable matching and conservative eligibility filtering."""

from __future__ import annotations

from .models import MatchResult, Opportunity, UserProfile


def _normalise(values: tuple[str, ...]) -> set[str]:
    return {value.strip().lower() for value in values if value.strip()}


def _shared_terms(left: set[str], right: set[str]) -> list[str]:
    """Match exact tags and sensible tag/subtag pairs (for example AI / ML-AI)."""
    return sorted(item for item in left if any(item == other or item in other or other in item for other in right))


def match_opportunity(profile: UserProfile, opportunity: Opportunity) -> MatchResult | None:
    """Score one opportunity, returning None only for explicit hard mismatches."""
    if opportunity.opportunity_type not in profile.opportunity_types:
        return None
    if not opportunity.remote and profile.location.strip().lower() != opportunity.location.strip().lower():
        return None

    score = 10  # Requested opportunity type.
    reasons = [f"Matches your requested {opportunity.opportunity_type} type."]
    uncertainties: list[str] = []

    profile_skills = _normalise(profile.skills)
    shared_skills = _shared_terms(profile_skills, _normalise(opportunity.skills))
    if shared_skills:
        score += 15 * len(shared_skills)
        reasons.append("Relevant skills: " + ", ".join(shared_skills) + ".")

    profile_interests = _normalise(profile.interests)
    shared_interests = _shared_terms(profile_interests, _normalise(opportunity.interests))
    if shared_interests:
        score += 10 * len(shared_interests)
        reasons.append("Aligned interests: " + ", ".join(shared_interests) + ".")

    if opportunity.remote:
        if profile.remote_ok:
            score += 10
            reasons.append("Remote participation is available.")
        else:
            uncertainties.append("This is remote; confirm it fits your preference.")
    else:
        score += 10
        reasons.append(f"Located in your stated location: {opportunity.location}.")

    levels = _normalise(opportunity.experience_levels)
    profile_level = profile.experience_level.strip().lower()
    if levels:
        if profile_level in levels:
            score += 10
            reasons.append(f"Lists {profile.experience_level} as a supported experience level.")
        else:
            uncertainties.append("Your experience level is not explicitly listed; check eligibility.")
    else:
        uncertainties.append("Experience-level eligibility was not provided.")

    if opportunity.deadline is None:
        uncertainties.append("No deadline is available; verify it at the source.")
    if opportunity.eligibility_note:
        uncertainties.append(opportunity.eligibility_note)

    return MatchResult(opportunity, score, tuple(reasons), tuple(uncertainties))


def rank_opportunities(profile: UserProfile, opportunities: list[Opportunity]) -> list[MatchResult]:
    matches = [match_opportunity(profile, opportunity) for opportunity in opportunities]
    return sorted((match for match in matches if match), key=lambda match: match.score, reverse=True)

