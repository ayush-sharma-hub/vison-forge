"""Live, source-linked opportunity retrieval adapters."""

from __future__ import annotations

from datetime import datetime
import re

import requests

from .models import Opportunity


DEVPOST_API_URL = "https://devpost.com/api/hackathons"


class SourceUnavailableError(RuntimeError):
    """Raised when a live source cannot be contacted or decoded safely."""


def _deadline_from_period(value: str) -> datetime.date | None:
    """Extract the final date from Devpost's human-readable date range."""
    match = re.search(r"([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})\s*$", value)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(0), "%b %d, %Y").date()
    except ValueError:
        return None


def fetch_devpost_hackathons(timeout_seconds: int = 15) -> list[Opportunity]:
    """Fetch currently open hackathons from Devpost's public listing endpoint.

    The upstream response does not consistently supply an exact deadline or eligibility
    details, so those fields remain explicit uncertainties rather than guesses.
    """
    try:
        response = requests.get(DEVPOST_API_URL, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise SourceUnavailableError(f"Devpost could not be retrieved: {error}") from error

    listings = payload.get("hackathons")
    if not isinstance(listings, list):
        raise SourceUnavailableError("Devpost returned an unexpected response format.")

    opportunities: list[Opportunity] = []
    for item in listings:
        if not isinstance(item, dict) or item.get("open_state") != "open":
            continue
        title, url = item.get("title"), item.get("url")
        if not isinstance(title, str) or not isinstance(url, str) or not url.startswith("https://"):
            continue
        location_data = item.get("displayed_location") or {}
        location = location_data.get("location") if isinstance(location_data, dict) else None
        location = location if isinstance(location, str) else "Location not provided"
        themes = item.get("themes") or []
        interests = tuple(
            theme["name"] for theme in themes
            if isinstance(theme, dict) and isinstance(theme.get("name"), str)
        )
        period = item.get("submission_period_dates")
        period = period if isinstance(period, str) else ""
        deadline = _deadline_from_period(period)
        organizer = item.get("organization_name")
        organizer = organizer if isinstance(organizer, str) and organizer else "Organizer not provided"
        remote = location.strip().lower() in {"online", "remote", "virtual"}
        note = "Verify eligibility, rules, and the submission deadline on the official event page."
        if period:
            note = f"Devpost reports submission period: {period}. {note}"
        opportunities.append(
            Opportunity(
                title=title,
                organizer=organizer,
                opportunity_type="hackathon",
                location=location,
                remote=remote,
                deadline=deadline,
                source_url=url,
                interests=interests,
                skills=(),
                experience_levels=(),
                eligibility_note=note,
                source_label="live Devpost listing",
            )
        )
    return opportunities
