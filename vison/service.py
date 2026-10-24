"""The action workflow used by the local CLI and ASI:One chat agent."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re

from .live_sources import SourceUnavailableError, fetch_devpost_hackathons
from .matching import rank_opportunities
from .models import UserProfile


@dataclass(frozen=True)
class SearchRequest:
    interests: tuple[str, ...]
    skills: tuple[str, ...]
    location: str
    remote_ok: bool
    experience_level: str


def _keywords(text: str, candidates: tuple[str, ...]) -> tuple[str, ...]:
    lower = text.lower()
    return tuple(item for item in candidates if item in lower)


def parse_search_request(text: str) -> SearchRequest:
    """Conservative offline fallback for a natural-language agent request.

    ASI:One routes the chat request to Vison. This parser keeps the execution path
    available when an LLM key is unavailable; it never claims missing preferences
    were supplied by the user.
    """
    interests = _keywords(text, ("ai", "machine learning", "data", "web", "climate", "health", "gaming", "security", "accessibility", "blockchain"))
    skills = _keywords(text, ("python", "javascript", "typescript", "java", "sql", "react", "design", "figma"))
    experience = "student" if any(word in text.lower() for word in ("student", "beginner", "college")) else "not provided"
    location_match = re.search(r"\b(?:in|from)\s+([A-Z][A-Za-z .-]{2,40})", text)
    location = location_match.group(1).strip(" .") if location_match else "not provided"
    remote_ok = not any(phrase in text.lower() for phrase in ("in person only", "onsite only", "not remote"))
    return SearchRequest(interests, skills, location, remote_ok, experience)


def interpret_request(text: str) -> SearchRequest:
    """Use ASI:One to understand a free-form request, with a safe local fallback.

    Only information stated by the user is retained. The fallback makes the live tool
    usable during development when a developer has not added an API key yet.
    """
    api_key = os.getenv("ASI_ONE_API_KEY")
    if not api_key:
        return parse_search_request(text)
    try:
        from openai import OpenAI

        client = OpenAI(base_url="https://api.asi1.ai/v1", api_key=api_key)
        response = client.chat.completions.create(
            model="asi1",
            temperature=0,
            max_tokens=300,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract only preferences explicitly present in the user's hackathon request. "
                        "Return a JSON object with interests (array of strings), skills (array of strings), "
                        "location (string or 'not provided'), remote_ok (boolean), and experience_level "
                        "(string or 'not provided'). Do not add skills, locations, eligibility, or dates."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        interests = tuple(str(value).strip() for value in data.get("interests", []) if str(value).strip())
        skills = tuple(str(value).strip() for value in data.get("skills", []) if str(value).strip())
        location = str(data.get("location") or "not provided").strip()
        experience = str(data.get("experience_level") or "not provided").strip()
        remote_ok = bool(data.get("remote_ok", True))
        return SearchRequest(interests, skills, location, remote_ok, experience)
    except Exception:
        # A live search is still more helpful than failing because intent enrichment is unavailable.
        return parse_search_request(text)


def run_live_hackathon_search(text: str, limit: int = 5) -> str:
    """Execute Vison's primary action: retrieve, rank, and explain live opportunities."""
    request = interpret_request(text)
    profile = UserProfile(
        interests=request.interests,
        skills=request.skills,
        location=request.location,
        remote_ok=request.remote_ok,
        experience_level=request.experience_level,
        opportunity_types=("hackathon",),
    )
    try:
        live_listings = fetch_devpost_hackathons()
    except SourceUnavailableError as error:
        return f"I could not retrieve live hackathons right now. Please try again shortly. Details: {error}"

    results = rank_opportunities(profile, live_listings)[:limit]
    if not results:
        return "I checked the live Devpost feed but found no open hackathons that fit the stated location/remote preference. Try allowing remote events or refining your request."

    lines = ["I retrieved and ranked live Devpost hackathons. Verify all details on each official event page before applying."]
    for number, match in enumerate(results, start=1):
        item = match.opportunity
        deadline = item.deadline.isoformat() if item.deadline else "not published"
        lines.extend((
            f"\n{number}. {item.title} — match score {match.score}",
            f"Organizer: {item.organizer} | Location: {item.location} | Deadline: {deadline}",
            f"Official listing: {item.source_url}",
            "Why it matched: " + " ".join(match.reasons),
            "Please verify: " + " ".join(match.uncertainties),
        ))
    lines.extend((
        "\nRecommended next action:",
        f"Open the first listing, confirm eligibility and deadline, then prepare a project idea that demonstrates {', '.join(request.skills) if request.skills else 'your strongest relevant skills'}.",
    ))
    return "\n".join(lines)
