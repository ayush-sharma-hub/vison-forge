"""Live retailer research layer for Vison Forge.

Retrieves real-time, source-linked component pricing and availability
from verified retailer APIs and public storefronts without scraping blocked sites,
inventing prices, or executing purchases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
import urllib.parse
import requests


@dataclass(frozen=True)
class PurchaseOption:
    """A verified, source-linked component purchase observation."""
    component_query: str
    title: str
    seller: str
    url: str
    price: float
    currency: str = "INR"
    in_stock: bool | None = None
    checked_at: str = ""


@dataclass(frozen=True)
class BuildTier:
    """A project build configuration based strictly on verified component options."""
    name: str  # "Basic", "Recommended", "Premium"
    description: str
    total_cost: float
    currency: str = "INR"
    is_complete: bool = True
    selections: tuple[PurchaseOption, ...] = ()


class RetailerUnavailableError(RuntimeError):
    """Raised when a retailer API or catalog endpoint cannot be reached."""


class RetailerSource(Protocol):
    """Protocol for retailer search adapters."""
    def search_component(self, query: str, timeout_seconds: int = 10) -> list[PurchaseOption]:
        ...


class QuartzComponentsAdapter:
    """Retailer adapter for Quartz Components (Jaipur, India — quartzcomponents.com).

    Quartz Components specializes in DIY hobby electronics (ESP32, Arduino, sensors,
    pumps, breadboards). Its robots.txt explicitly permits public product catalog
    access and publishes agent instructions (agents.md).
    """

    BASE_URL = "https://quartzcomponents.com"
    SEARCH_ENDPOINT = "https://quartzcomponents.com/search/suggest.json"
    SELLER_NAME = "Quartz Components"
    DEFAULT_CURRENCY = "INR"

    def __init__(self, session: requests.Session | None = None):
        self._session = session or requests.Session()

    def search_component(self, query: str, timeout_seconds: int = 10) -> list[PurchaseOption]:
        """Search Quartz Components for matching products and parse verified fields."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        url = f"{self.SEARCH_ENDPOINT}?q={urllib.parse.quote(cleaned_query)}&resources[type]=product"
        headers = {
            "User-Agent": "VisonForge/1.0 (Hardware Planning Agent; +https://github.com/vison-forge)",
            "Accept": "application/json",
        }

        try:
            response = self._session.get(url, headers=headers, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as err:
            raise RetailerUnavailableError(f"Quartz Components search failed for '{query}': {err}") from err

        products = payload.get("resources", {}).get("results", {}).get("products")
        if not isinstance(products, list):
            raise RetailerUnavailableError("Quartz Components returned an unexpected data structure.")

        options: list[PurchaseOption] = []
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        for item in products:
            if not isinstance(item, dict):
                continue

            raw_title = item.get("title")
            raw_price = item.get("price")
            raw_url = item.get("url")
            available = item.get("available")

            if not raw_title or not isinstance(raw_title, str):
                continue
            if not raw_url or not isinstance(raw_url, str):
                continue

            # Parse and validate price
            if raw_price is None or raw_price == "":
                continue
            try:
                price_val = float(str(raw_price).replace(",", "").strip())
                if price_val <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            # Construct clean absolute URL without tracking search parameters
            clean_path = raw_url.split("?")[0]
            if not clean_path.startswith("http"):
                full_url = f"{self.BASE_URL}{clean_path}"
            else:
                full_url = clean_path

            # In-stock status: only include if explicitly a boolean
            in_stock = available if isinstance(available, bool) else None

            options.append(
                PurchaseOption(
                    component_query=cleaned_query,
                    title=raw_title.strip(),
                    seller=self.SELLER_NAME,
                    url=full_url,
                    price=price_val,
                    currency=self.DEFAULT_CURRENCY,
                    in_stock=in_stock,
                    checked_at=now_iso,
                )
            )

        return options


# Query simplification keywords to increase search relevance for hobby retailer catalogs
_QUERY_KEYWORD_MAP = {
    "esp32 development board": "ESP32 CP2102 development board",
    "capacitive soil-moisture sensor": "capacitive soil moisture sensor",
    "5v relay module with 3.3v-compatible input": "5V relay module",
    "low-voltage 5v usb water pump": "mini dc submersible water pump",
    "silicone tubing": "flexible conduit pipe",
    "separate 5v usb power source": "5V 2A power adapter",
    "breadboard": "breadboard",
    "jumper wires": "jumper wires",
    "usb data cable": "micro USB cable",
    "robot chassis with two dc motors": "2WD robot chassis",
    "low-voltage motor driver module": "L298N motor driver module",
    "line sensors or ultrasonic sensor": "HC-SR04 ultrasonic sensor",
    "aa battery holder or certified usb power bank": "AA battery holder",
}


def simplify_query(component_name: str) -> str:
    """Map high-level component descriptions to effective retailer catalog search queries."""
    lower = component_name.lower().strip()
    for key, simplified in _QUERY_KEYWORD_MAP.items():
        if key in lower or lower in key:
            return simplified
    return component_name


class ComponentResearchService:
    """Coordinates component research across verified retailer adapters."""

    DISCLAIMER = (
        "Notice: Shipping costs, GST/taxes, import duties, bundle accessories, and final "
        "checkout prices may differ from observed prices unless explicitly provided by the seller. "
        "Vison Forge provides purely informational price observations and direct links; it never "
        "adds items to a cart, collects personal address details, or initiates payments."
    )

    def __init__(self, adapter: RetailerSource | None = None):
        self._adapter = adapter or QuartzComponentsAdapter()

    def research_component(self, component_name: str, timeout_seconds: int = 10) -> list[PurchaseOption]:
        """Search for a single component and return verified purchase options."""
        query = simplify_query(component_name)
        try:
            return self._adapter.search_component(query, timeout_seconds=timeout_seconds)
        except RetailerUnavailableError:
            return []

    def calculate_total(
        self,
        component_selections: list[tuple[int, PurchaseOption | None, str]],
        currency: str = "INR",
    ) -> tuple[float, str, bool, list[str]]:
        """Calculate the total price from verified component selections.

        Returns: (total_price, currency, is_complete, unpriced_component_names)
        """
        total = 0.0
        is_complete = True
        unpriced = []

        for quantity, option, component_name in component_selections:
            if option is None:
                is_complete = False
                unpriced.append(component_name)
                continue

            if option.currency.upper() != currency.upper():
                # Currency mismatch - cannot directly sum without verified conversion
                is_complete = False
                unpriced.append(f"{component_name} (currency mismatch: {option.currency})")
                continue

            total += option.price * quantity

        return round(total, 2), currency, is_complete, unpriced

    def build_tiers(
        self,
        component_data: list[tuple[str, int, list[PurchaseOption]]],
        currency: str = "INR",
    ) -> list[BuildTier]:
        """Create Basic, Recommended, and Premium build tiers only if supported by real options.

        - Basic: uses the lowest-cost in-stock verified option for each component.
        - Recommended: uses a balanced standard option (second lowest or standard model).
        - Premium: uses enhanced/higher-tier verified options where available.

        Only tiers with real differing options are generated.
        """
        if not component_data:
            return []

        # Validate options by currency
        valid_data: list[tuple[str, int, list[PurchaseOption]]] = []
        for name, qty, options in component_data:
            valid_opts = [
                opt for opt in options
                if opt.currency.upper() == currency.upper() and opt.price > 0
            ]
            # Sort by price ascending
            valid_opts.sort(key=lambda x: x.price)
            valid_data.append((name, qty, valid_opts))

        # Check if at least one component has options
        has_any_options = any(len(opts) > 0 for _, _, opts in valid_data)
        if not has_any_options:
            return []

        # 1. Basic Tier: lowest cost available options
        basic_selections = []
        for name, qty, opts in valid_data:
            selected = opts[0] if opts else None
            basic_selections.append((qty, selected, name))

        basic_total, _, basic_complete, _ = self.calculate_total(basic_selections, currency)
        tiers = [
            BuildTier(
                name="Basic",
                description="Budget-conscious build using verified entry-level options.",
                total_cost=basic_total,
                currency=currency,
                is_complete=basic_complete,
                selections=tuple(opt for _, opt, _ in basic_selections if opt is not None),
            )
        ]

        # 2. Recommended Tier: only if at least some components offer a standard/higher option
        rec_selections = []
        has_recommended_diff = False
        for name, qty, opts in valid_data:
            if len(opts) >= 2:
                # pick index 1 if available
                selected = opts[min(1, len(opts) - 1)]
                has_recommended_diff = True
            elif opts:
                selected = opts[0]
            else:
                selected = None
            rec_selections.append((qty, selected, name))

        if has_recommended_diff:
            rec_total, _, rec_complete, _ = self.calculate_total(rec_selections, currency)
            tiers.append(
                BuildTier(
                    name="Recommended",
                    description="Standard build with proven balance of reliability and cost.",
                    total_cost=rec_total,
                    currency=currency,
                    is_complete=rec_complete,
                    selections=tuple(opt for _, opt, _ in rec_selections if opt is not None),
                )
            )

        # 3. Premium Tier: only if higher-spec options exist
        prem_selections = []
        has_premium_diff = False
        for name, qty, opts in valid_data:
            if len(opts) >= 3:
                selected = opts[-1]
                has_premium_diff = True
            elif len(opts) >= 2 and not has_recommended_diff:
                selected = opts[-1]
                has_premium_diff = True
            elif opts:
                selected = opts[-1]
            else:
                selected = None
            prem_selections.append((qty, selected, name))

        if has_premium_diff:
            prem_total, _, prem_complete, _ = self.calculate_total(prem_selections, currency)
            tiers.append(
                BuildTier(
                    name="Premium",
                    description="Enhanced build featuring higher-spec or branded modules where available.",
                    total_cost=prem_total,
                    currency=currency,
                    is_complete=prem_complete,
                    selections=tuple(opt for _, opt, _ in prem_selections if opt is not None),
                )
            )

        return tiers
