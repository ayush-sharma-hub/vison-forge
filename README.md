# Vison Forge

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

Vison Forge is an AI hardware-project planning agent for students, makers, robotics teams, and hackathon builders. It turns a low-voltage Arduino, ESP32, Raspberry Pi, or simple robotics idea into a safe, buildable project pack.

> **Current scope:** Vison Forge produces deterministic feasibility checks, component requirements, safety notes, wiring guidance, build steps, tests, team tasks, timelines, a submission checklist, local Markdown artifacts, and **live source-linked retailer component research** (direct purchase URLs, observed prices in ₹/INR, seller names, stock availability, price timestamps, and transparent project totals). It intentionally never invents prices or retailer listings.

## Run the MVP

From this folder in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

Try: `I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2.` Then choose whether to create the local build-pack files.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Run the ASI:One-compatible agent

1. Install the additional agent dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env`, then set a new private `VISON_AGENT_SEED`. Do not commit this file.

3. Start the agent:

   ```powershell
   python agent.py
   ```

The process publishes the standard Agent Chat Protocol manifest and prints an Agentverse inspector URL. In the inspector, connect a mailbox; then use the Agent Profile / Chat with Agent path to open it in ASI:One. Try: `I want an ESP32 plant watering system for two plants, under ₹2500, in 7 days, for a beginner team of 2.`

An agent becomes publicly discoverable only after it is running, its mailbox is connected, and its Agentverse profile is completed. This repository does not claim registration until those steps have succeeded with your account.

## Live source and verification policy

- **Component Retailer Source:** Quartz Components (`https://quartzcomponents.com`), a major Indian electronics distributor for Arduino, ESP32, Raspberry Pi, robotics, sensors, and low-voltage prototyping parts.
  - **Access & Terms:** Public product catalog endpoint (`/search/suggest.json`). Quartz Components explicitly permits storefront crawling in its `robots.txt` and publishes dedicated agent guidelines in `agents.md` (`https://quartzcomponents.com/agents.md`). No API key or account creation is required for informational product search.
  - **Verified Fields:** Only actual fields returned by the source are retained: component query, seller name (`Quartz Components`), product title, direct purchase URL, displayed price (INR), stock status (`in_stock` boolean), and price-check timestamp.
  - **Tiers & Total:** Basic, Recommended, and Premium options are computed only when supported by multiple real compatible options. Transparent project totals sum verified item prices without guessing unknown values.
  - **Purchasing Safety Policy:** Vison Forge is strictly an informational planning agent. It **never** adds items to a shopping cart, places orders, asks for addresses, or handles payment details. Shipping costs, local taxes (GST), import duties, bundle contents, and final checkout totals must be confirmed by the user on the seller's website.
  - **Graceful Failure:** If the retailer is unreachable or returns no listing for a part, the price is clearly marked as unavailable rather than using synthetic or sample data.

## Project layout

- `main.py` — interactive local Vison Forge workflow
- `vison/forge.py` — safety gate, planning logic, BOM generation, and build-pack files
- `vison/forge_service.py` — natural-language request parsing and response formatting
- `vison/retailer.py` — live retailer adapter (Quartz Components), tier calculations, and purchase policy
- `agent.py` — ACP-compatible uAgent entry point for ASI:One
- `tests/test_forge.py` — project planning, safety gate, and build-pack tests
- `tests/test_retailer.py` — mocked retailer tests (success, unavailability, missing price, currency mismatch, totals)

## Honest project status

- [x] Local project-planning workflow
- [x] Safety gate, compatibility notes, difficulty score, team tasks, timeline, tests, and artifact generation
- [x] Live retailer price, stock, and direct-purchase-link research (Quartz Components / INR)
- [x] Basic, Recommended, and Premium tier calculations from real observed options
- [x] Focused tests with mocked retailer responses (success, offline source, missing prices, currency mismatch, totals)
- [ ] Photo-based progress verification (planned stretch goal)
- [x] ACP-compatible uAgent implementation
- [ ] Agentverse mailbox connection and public registration (requires your account)
- [ ] ASI:One live-chat verification and shared-chat URL (requires your account)
- [ ] Deployment and submission evidence

This repository does **not** yet claim ASI:One discovery, Agentverse registration, live listings, or deployment.
