"""Unit tests for the Vison Forge live retailer research layer."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import requests

from vison.retailer import (
    BuildTier,
    ComponentResearchService,
    PurchaseOption,
    QuartzComponentsAdapter,
    RetailerUnavailableError,
)
from vison.forge import Component, ForgePlan, ForgeRequest, create_plan, render_build_pack


class RetailerAdapterTests(unittest.TestCase):
    """Tests for the QuartzComponentsAdapter and mocked responses."""

    def test_successful_source_result(self):
        """Verify successful response parsing with verified fields."""
        mock_payload = {
            "resources": {
                "results": {
                    "products": [
                        {
                            "title": "ESP32 30 Pin CP2102 Development Board",
                            "price": "375.00",
                            "url": "/products/esp32-development-board?ref=123",
                            "available": True,
                        }
                    ]
                }
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_payload

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        adapter = QuartzComponentsAdapter(session=mock_session)
        options = adapter.search_component("ESP32")

        self.assertEqual(len(options), 1)
        opt = options[0]
        self.assertEqual(opt.title, "ESP32 30 Pin CP2102 Development Board")
        self.assertEqual(opt.seller, "Quartz Components")
        self.assertEqual(opt.price, 375.0)
        self.assertEqual(opt.currency, "INR")
        self.assertTrue(opt.in_stock)
        self.assertEqual(opt.url, "https://quartzcomponents.com/products/esp32-development-board")
        self.assertTrue(bool(opt.checked_at))

    def test_unavailable_source_raises_error(self):
        """Verify network/server failures raise RetailerUnavailableError."""
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.ConnectionError("Connection refused")

        adapter = QuartzComponentsAdapter(session=mock_session)
        with self.assertRaises(RetailerUnavailableError):
            adapter.search_component("ESP32")

    def test_missing_or_invalid_price_is_skipped(self):
        """Verify products without valid prices are filtered out."""
        mock_payload = {
            "resources": {
                "results": {
                    "products": [
                        {"title": "Item with None price", "price": None, "url": "/p/1", "available": True},
                        {"title": "Item with empty price", "price": "", "url": "/p/2", "available": True},
                        {"title": "Item with invalid price", "price": "free", "url": "/p/3", "available": True},
                        {"title": "Item with zero price", "price": "0.00", "url": "/p/4", "available": True},
                        {"title": "Valid item", "price": "42.50", "url": "/p/5", "available": True},
                    ]
                }
            }
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_payload
        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        adapter = QuartzComponentsAdapter(session=mock_session)
        options = adapter.search_component("Relay")

        self.assertEqual(len(options), 1)
        self.assertEqual(options[0].title, "Valid item")
        self.assertEqual(options[0].price, 42.5)


class ComponentResearchServiceTests(unittest.TestCase):
    """Tests for price calculation, currency checks, and tier construction."""

    def test_total_calculation_with_quantities(self):
        """Verify transparent total calculation with component quantities."""
        service = ComponentResearchService(adapter=MagicMock())
        opt_esp32 = PurchaseOption(
            component_query="esp32", title="ESP32", seller="Quartz Components",
            url="https://quartzcomponents.com/esp32", price=375.0, currency="INR", in_stock=True
        )
        opt_sensor = PurchaseOption(
            component_query="sensor", title="Moisture Sensor", seller="Quartz Components",
            url="https://quartzcomponents.com/sensor", price=52.0, currency="INR", in_stock=True
        )

        selections = [
            (1, opt_esp32, "ESP32 Board"),
            (2, opt_sensor, "Soil Sensor"),
        ]
        total, currency, is_complete, unpriced = service.calculate_total(selections, currency="INR")

        self.assertEqual(total, 479.0)  # 1 * 375 + 2 * 52
        self.assertEqual(currency, "INR")
        self.assertTrue(is_complete)
        self.assertEqual(unpriced, [])

    def test_total_calculation_with_missing_price(self):
        """Verify incomplete total when a component has no verified price."""
        service = ComponentResearchService(adapter=MagicMock())
        opt_esp32 = PurchaseOption(
            component_query="esp32", title="ESP32", seller="Quartz Components",
            url="https://quartzcomponents.com/esp32", price=375.0, currency="INR", in_stock=True
        )

        selections = [
            (1, opt_esp32, "ESP32 Board"),
            (1, None, "Special Custom Sensor"),
        ]
        total, currency, is_complete, unpriced = service.calculate_total(selections, currency="INR")

        self.assertEqual(total, 375.0)
        self.assertFalse(is_complete)
        self.assertIn("Special Custom Sensor", unpriced)

    def test_currency_mismatch_prevents_erroneous_sum(self):
        """Verify foreign currency options are not added to INR total without conversion."""
        service = ComponentResearchService(adapter=MagicMock())
        opt_usd = PurchaseOption(
            component_query="esp32", title="ESP32 USD", seller="Global Store",
            url="https://example.com/esp32", price=15.0, currency="USD", in_stock=True
        )

        selections = [(1, opt_usd, "ESP32")]
        total, currency, is_complete, unpriced = service.calculate_total(selections, currency="INR")

        self.assertEqual(total, 0.0)
        self.assertFalse(is_complete)
        self.assertTrue(any("currency mismatch" in item for item in unpriced))

    def test_build_tiers_generation(self):
        """Verify Basic, Recommended, and Premium tiers are generated only when options exist."""
        service = ComponentResearchService(adapter=MagicMock())
        opt_basic = PurchaseOption("esp32", "ESP32 Basic", "Store", "http://1", 350.0, "INR", True)
        opt_rec = PurchaseOption("esp32", "ESP32 Standard", "Store", "http://2", 375.0, "INR", True)
        opt_prem = PurchaseOption("esp32", "ESP32 Camera", "Store", "http://3", 675.0, "INR", True)

        component_data = [("ESP32", 1, [opt_basic, opt_rec, opt_prem])]
        tiers = service.build_tiers(component_data, currency="INR")

        self.assertEqual(len(tiers), 3)
        tier_names = [t.name for t in tiers]
        self.assertEqual(tier_names, ["Basic", "Recommended", "Premium"])
        self.assertEqual(tiers[0].total_cost, 350.0)
        self.assertEqual(tiers[1].total_cost, 375.0)
        self.assertEqual(tiers[2].total_cost, 675.0)

    def test_plan_with_research_service_integration(self):
        """Verify integration of research service with Forge plan and build-pack rendering."""
        mock_adapter = MagicMock()
        mock_adapter.search_component.return_value = [
            PurchaseOption("esp32", "ESP32 Dev Board", "Quartz Components", "https://quartzcomponents.com/esp32", 375.0, "INR", True, "2026-10-24")
        ]
        service = ComponentResearchService(adapter=mock_adapter)

        request = ForgeRequest(
            idea="ESP32 plant watering system",
            platform="esp32",
            budget=2500,
            deadline_days=7,
        )
        plan = create_plan(request, research_service=service)

        self.assertEqual(plan.verdict, "Ready")
        self.assertIsNotNone(plan.estimated_total)
        self.assertTrue(plan.estimated_total > 0)
        self.assertIn("Quartz Components", plan.research_status)

        build_pack = render_build_pack(request, plan)
        self.assertIn("Bill of Materials", build_pack["BOM.md"])
        self.assertIn("Quartz Components", build_pack["BOM.md"])
        self.assertIn("Important Purchasing Policy", build_pack["BOM.md"])
        self.assertIn("Important Purchasing Policy", build_pack["README.md"])
