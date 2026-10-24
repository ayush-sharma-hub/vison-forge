# Vison Forge — Implementation Plan

## 1. Product decision

**Vison Forge** is an AI hardware-project planning agent for students, makers, robotics teams, and hackathon builders.

Its single purpose is to transform a hardware idea into a practical, buildable project pack. It is not a general chatbot, a generic coding assistant, or an automatic purchasing tool.

**Positioning:**

> Describe a device you want to build. Vison Forge creates a realistic plan to build, test, document, and present it.

## 2. The real problem

Beginners often abandon Arduino, ESP32, Raspberry Pi, and robotics ideas because they cannot confidently answer:

- What parts do I actually need?
- Which parts work together?
- What should I build first?
- Is this feasible within my budget, deadline, and skill level?
- How do I test it and present it as a finished project?

Vison Forge reduces planning uncertainty before the user buys parts or writes code.

## 3. Focused first-release scope

### Supported project families

The first release supports only:

- Arduino and ESP32 sensor/automation projects
- beginner Raspberry Pi projects
- line-following, obstacle-avoiding, and simple IoT robotics projects

### Explicitly out of scope for the first release

- medical devices, drones, weapons, mains-voltage work, or other hazardous systems
- autonomous purchasing, payments, or ordering components
- bespoke PCB design and advanced electrical certification
- arbitrary software-only projects
- diagnosing a physically damaged device from an image

These constraints make Vison Forge reliable and safe enough to demonstrate.

## 4. Primary ASI:One workflow

### Example user request

> I want to make an ESP32 plant-watering system for two plants. I am a beginner, have a budget of ₹2,500, and need a demo in seven days.

### Agent workflow

1. **Understand the goal**
   - Extract the intended device, number of inputs/outputs, experience level, budget, deadline, available parts, and project setting.

2. **Ask only missing critical questions**
   - Example: “Do you have Wi-Fi where the device will run?”
   - Example: “Should the pump use a wall outlet or a low-voltage supply?”

3. **Run the feasibility check**
   - Determine whether the request fits the supported scope.
   - Identify risks: unsafe power, insufficient budget, unrealistic deadline, missing hardware.
   - Offer a smaller safe version if necessary.

4. **Retrieve real reference material**
   - Use manufacturer documentation and trusted component sources for board pinouts, voltage limits, library links, and compatibility facts.
   - Preserve source URLs. Never invent a component specification or price.

5. **Research purchase options**
   - Search trusted component retailers relevant to the user's country and currency.
   - Return one or more source-linked options for each required component, including the observed price, seller, stock status when available, and the time the price was checked.
   - Calculate an estimated total from only the displayed source prices.
   - Mark shipping, import duties, taxes, bundle contents, and out-of-stock status as unknown unless the source explicitly provides them.
   - Give the user direct purchase links so they can choose and order the parts themselves.

6. **Create the Vison Forge Build Pack**
   - Project brief
   - architecture overview
   - bill of materials (BOM) with quantities, price observations, seller options, and direct purchase links
   - compatibility and safety notes
   - ordered build plan
   - testing plan
   - demo and submission checklist
   - team task split, when applicable

7. **Create useful artifacts after confirmation**
   - Generate `README.md`, `BUILD_PLAN.md`, `BOM.md`, and `TEST_PLAN.md` locally or in a connected repository.
   - Create task-board items or GitHub issues only after the user explicitly approves the connected-account action.

7. **Return an actionable summary in ASI:One**
   - State what it created, top risks, first task, and links/paths to the build-pack artifacts.

## 5. What makes it an agent rather than a chatbot

Vison Forge must complete a tool-driven workflow:

```text
User idea
  → requirements extraction
  → feasibility and safety gate
  → documentation/component research
  → compatibility checks
  → build-pack generation
  → optional approved repository/task creation
  → test and demo plan
```

The user receives structured project artifacts and an execution plan—not merely a paragraph of advice.

## 6. Minimum viable product (MVP)

The MVP should reliably make a complete build pack for one supported project request.

### Inputs

- Project idea in plain language
- Supported platform: Arduino, ESP32, Raspberry Pi, or simple robotics
- Experience level: beginner / intermediate
- Budget and currency
- Deadline
- Available components, if any
- Team size, if relevant

### Outputs

- Feasibility verdict: **Ready**, **Needs clarification**, or **Scale down**
- Component list with quantities and reasons
- Retailer options with direct purchase links, observed price, price-check time, and stock status when available
- Approximate component and project total only when supported by real source prices; otherwise label price as unknown
- Wiring/connection guidance in text form
- Ordered build tasks
- Test cases and pass criteria
- Safety warnings
- Source links
- Generated Markdown build pack

## 6A. Feature set

These features remain within Vison Forge's single purpose: turning a hardware idea into a safe, affordable, buildable project.

### Core engineering features

- **Compatibility checker** — evaluates voltage, power requirements, pins, and communication protocols between selected components. It explains incompatible selections and proposes a supported alternative only when sourced.
- **Budget optimizer** — presents Basic, Recommended, and Premium builds with transparent component totals and purchase links.
- **Already-have-parts mode** — removes components the user owns from the shopping list while retaining them in the wiring and compatibility checks.
- **Circuit/wiring blueprint** — generates a text connection table, for example `ESP32 GPIO 34 → capacitive soil sensor output`.
- **Safety gate** — stops or scales down requests involving mains power, high-current batteries, water near electricity, drones, medical devices, weapons, or hazardous machinery.
- **Build difficulty score** — reports estimated complexity, time, risk, required skills, and likely blockers.
- **Failure simulator** — lists likely build failures, diagnostic tests, expected observations, and safe recovery actions.

### Execution and delivery features

- **Team task allocator** — assigns hardware, firmware, testing, documentation, and demo tasks based on team size and skills.
- **Project timeline** — creates an ordered, deadline-aware plan with time reserved for testing and recovery.
- **Build journal** — records user progress updates such as “sensor test complete” and recalculates remaining work.
- **Project README generator** — produces a source-linked repository README, setup guide, BOM, architecture, and test instructions.
- **Hackathon submission mode** — produces a problem statement, innovation explanation, architecture outline, demo script, and submission checklist.
- **Progress-photo verification** — a later visual feature where the user provides a build photo; Vison Forge compares it against the planned setup and reports only visible, non-safety-critical discrepancies. It must advise human review before any physical modification.

### MVP success criteria

- [ ] A user completes the workflow directly through ASI:One.
- [ ] The agent uses at least one real research/documentation tool.
- [ ] The result contains a concrete, source-linked build pack.
- [ ] The agent refuses unsupported or unsafe hardware work clearly.
- [ ] A user can save or create the planning artifacts from the chat workflow.

## 7. Tool and data plan

| Need | Tool/data source | Agent action |
|---|---|---|
| Intent understanding | ASI:One model | Extract structured requirements and ask only critical follow-ups. |
| Board documentation | Official Arduino, Espressif, Raspberry Pi documentation | Verify pin, voltage, and library information. |
| Component information | Trusted electronics distributors/manufacturer pages | Check descriptions and compatibility facts. |
| Prices and purchase links | Country-appropriate authorized distributors and component retailers | Search component listings, retain seller URL, price, availability, and timestamp; calculate a transparent estimate. |
| Project artifacts | Local files or GitHub API | Create the approved build-pack documents. |
| Task tracking, optional | GitHub Issues or a task-board integration | Create tasks only with user approval. |

No secret or account token belongs in source code. Keys remain in `.env` and are excluded from Git.

## 8. Proposed architecture

```text
ASI:One Chat (ACP)
      │
      ▼
Vison Forge uAgent
      │
      ├── Requirements interpreter
      ├── Safety and scope gate
      ├── Research / documentation retriever
      ├── Compatibility evaluator
      ├── Build-pack generator
      └── Approved artifact publisher
              │
              ├── Local Markdown files
              └── Optional GitHub issues/repository files
```

## 9. Safety and honesty rules

- Never advise work on mains electricity, high-current batteries, weapons, medical devices, or dangerous machinery in the MVP.
- Never claim a component is compatible unless a source supports it.
- Never invent a component price, seller, discount, delivery time, stock status, tax, or purchase link.
- Treat prices as time-sensitive: display the retailer, currency, and the time checked; tell users to confirm the final price and delivery terms on the seller page.
- Show multiple sellers where practical, but do not claim one is the best unless the comparison criterion is stated.
- Link users directly to seller pages, but never place an order, add items to a cart, enter payment details, or share a user address.
- Label estimates, unknown prices, and unverified details clearly.
- Use official documentation whenever possible.
- Never purchase, publish to a repository, or contact a third party without explicit user approval.
- When an idea is unsafe or outside scope, explain why and propose a safe, lower-risk alternative.

## 10. Build milestones

### Milestone A — Product pivot and local logic

- Replace opportunity-matching terminology with Vison Forge project-planning terminology.
- Define structured project requirements and support boundaries.
- Create deterministic feasibility and safety checks.
- Add difficulty scoring, compatibility checking, already-have-parts filtering, team allocation, timeline generation, and failure simulation.
- Add tests for supported, incomplete, and unsafe requests.

### Milestone B — Build-pack generation

- Generate a consistent Markdown build pack from a validated request.
- Include BOM, purchase options, wiring table, build sequence, tests, risks, timeline, team tasks, README, and hackathon submission pack.
- Add an updateable local build journal.
- Add artifact previews and focused tests.

### Milestone C — Live research tools (Completed)

- **Selected Retailer:** Quartz Components (`https://quartzcomponents.com`, Jaipur, India).
  - Specializes in hobby electronics: ESP32, Arduino, Raspberry Pi, sensors, DC pumps, relays, breadboards, jumper wires.
  - Technically accessible via standard public catalog endpoint: `/search/suggest.json`.
  - Terms & robots.txt: Expressly allows storefront crawling and publishes dedicated agent guidelines in `agents.md`.
  - Authentication: None required for product discovery.
  - Reliability & Currency: Real-time INR pricing, explicit stock availability boolean, direct canonical URLs.
- **Retailer Adapter (`vison/retailer.py`):**
  - Extracts verified fields only: `component_query`, `title`, `seller`, `url`, `price`, `currency`, `in_stock`, and `checked_at` timestamp.
  - Never fabricates prices or stock levels.
  - Handles network failures and invalid payloads with `RetailerUnavailableError`.
- **Tier & Total Calculation:**
  - Calculates transparent project totals summing verified component costs.
  - Generates Basic, Recommended, and Premium tiers strictly when multiple real compatible options are retrieved.
  - Identifies unpriced or currency-mismatched items and flags partial estimates.
- **Safety Policy:**
  - Strict read-only purchasing assistance: never adds to cart, collects address details, or handles payments.
  - Transparent disclosure that shipping, GST, duties, and checkout totals may vary.
- **Tests:**
  - 13 comprehensive unit and integration tests covering successful retrieval, network unavailability, missing prices, currency mismatch, totals, safety gates, and build packs.

### Milestone D — ASI:One / ACP integration

- Replace the current opportunity workflow in the ACP agent with Vison Forge.
- Confirm the full project-plan workflow works in ASI:One.
- Publish a clear Agentverse profile describing the supported hardware scope.

### Milestone E — Optional actions and submission package

- Add user-approved local file generation.
- Optionally add user-approved GitHub issue/file creation.
- Prepare the README, test evidence, Agentverse URL, ASI:One shared-chat URL, and demo video.

### Milestone F — Visual progress verification

- Add an image-input flow only after the text planning workflow is reliable.
- Compare an uploaded progress photo to the approved wiring/assembly plan.
- Report visible component and connection discrepancies conservatively.
- Require user confirmation and human review; do not claim that a photo proves electrical safety.

## 11. Demo scenario

Use one simple, truthful project for the final demo:

> “Build a low-cost ESP32 soil-moisture monitor for two plants, under ₹2,500, in seven days, for a beginner team of two.”

The demo should show Vison Forge:

1. Asking one or two clarifying questions.
2. Checking feasibility and safety.
3. Retrieving documentation.
4. Finding compatible component options from relevant retailers, with live purchase links and a transparent estimated total.
5. Producing the build pack.
6. Creating the approved `README.md` and task checklist.
7. Explaining the first build task and test condition.

## 12. Approval gate

**No implementation work should begin until this plan is approved.**

After approval, begin with Milestone A only. Do not add external-account integrations, use secrets, or replace the existing agent workflow until the local Vison Forge planning flow is tested.
