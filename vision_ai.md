# Vison AI — Project Guide & AI Coding Prompt

> **Purpose:** Use this file as the single source of context when asking an AI coding assistant to build the Vison AI agent step by step.
>
> **Current setup:** Python 3.11.9 is installed. A virtual environment (`.venv`) has been created and activated. `requests` and `python-dotenv` have been installed.
>
> **Important:** The project idea below is the currently proposed direction. Confirm it with your team and check it against the official Fetch-A-Thon 3.0 challenge rules before submission.

---

## 1. Project identity

- **Project name:** Vison AI
- **Challenge:** Fetch-A-Thon 3.0 — ASI:One Agent Challenge
- **Working concept:** An AI opportunity-finder that helps users discover relevant hackathons and internships, checks matches against a user profile, ranks opportunities, highlights deadlines, and suggests next steps.
- **Main goal:** Build a useful, demonstrable agent—not just a chatbot that describes what it could do.
- **Team size:** 2–4 people
- **Skill assumption:** Beginner-friendly Python; explain commands and code changes clearly.

## 2. What Vison should do

### Minimum viable product (MVP)
1. Accept a simple user profile: interests, skills, location/remote preference, experience level, and opportunity type.
2. Retrieve opportunities from a real, accessible source/API when possible.
3. Normalize results into a consistent format.
4. Filter or score opportunities against the user's stated preferences and eligibility.
5. Show title, organizer/company, type, location/remote status, deadline (if available), source link, match reason, and any uncertainty.
6. Give a short action plan for the best matches.
7. Be honest when data or deadlines cannot be verified. Never invent listings, eligibility rules, or dates.

### Suggested first release
Start with **hackathons and internships** only. Keep the first version small and working. If a reliable source/API is not available, clearly explain the limitation and use a small, clearly labelled sample dataset only for local testing—not as live results.

## 3. Competition and delivery checklist

Verify every item against the current official challenge materials; do not assume that a suggested architecture automatically satisfies the rules.

- [ ] A working agent with a clear use case and an end-to-end workflow.
- [ ] Real task execution through tools/APIs where appropriate.
- [ ] Compatibility with the required Fetch.ai / ASI:One agent flow and protocols.
- [ ] Agent registered/deployed on the platform required by the challenge.
- [ ] The primary workflow can be demonstrated through ASI:One if required by the rules.
- [ ] Public GitHub repository with setup instructions and a useful README.
- [ ] Required ASI:One shared-chat URL and Agentverse profile URL(s), if required.
- [ ] A 3–5 minute demo video, if required.
- [ ] Project categorized/tagged as required by the challenge. If the official instructions still request these badges, include:
  - `![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)`
  - `![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)`

Official starting references:
- Fetch-A-Thon Hackpack: https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack
- uAgents documentation: https://uagents.fetch.ai/docs/
- Agentverse documentation: https://docs.agentverse.ai/

Read the current challenge requirements before finalizing the architecture or submission checklist.

## 4. Current development environment

- Python: `3.11.9`
- Virtual environment folder: `.venv`
- Installed packages: `requests`, `python-dotenv`
- Intended editor: VS Code
- Run Python commands from the project folder with `.venv` activated.

If activation is needed in PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

If packages need to be installed:
```powershell
python -m pip install --upgrade pip
pip install requests python-dotenv
```

## 5. Proposed simple project structure

Ask the coding AI to create only the files needed for the next working milestone. Avoid generating a huge project all at once.

```text
vison/
├── .venv/                  # local environment; do not commit
├── .env                    # secrets/API keys; do not commit
├── .env.example            # names of required environment variables, no secrets
├── .gitignore
├── README.md
├── requirements.txt
├── main.py                 # entry point
├── vison/
│   ├── __init__.py
│   ├── models.py            # normalized opportunity data structure
│   ├── matching.py          # profile matching and ranking
│   └── sources.py           # opportunity retrieval adapters
└── tests/
    └── test_matching.py
```

This is a proposed structure, not a requirement. The AI should explain any changes before making them.

## 6. Master prompt — paste this into your AI coding assistant

You are my senior Python engineer and hackathon mentor. Help me build **Vison AI**, a beginner-friendly but genuinely useful AI agent for Fetch-A-Thon 3.0 — ASI:One Agent Challenge.

### My setup and skill level
- I use Windows and VS Code.
- Python 3.11.9 is installed.
- I have created and activated `.venv`.
- I installed `requests` and `python-dotenv`.
- I know basic Python and need clear, step-by-step guidance.

### Product direction
Vison helps users find hackathons and internships that fit their skills, interests, location/remote preference, and experience. It retrieves opportunities from real sources when possible, scores and explains matches, surfaces deadlines with source links, and recommends practical next steps.

### Engineering rules
1. First inspect the existing project files and ask me to share their contents if you cannot inspect the workspace directly. Do not overwrite files blindly.
2. Work in **small, testable milestones**. Start with the smallest useful local MVP, then integrate the official agent protocol/platform.
3. Before each milestone, state its goal and list the files you will create/change.
4. Give exact Windows PowerShell commands and exact file paths. Explain where to run each command.
5. If you provide code, provide complete copy-paste-ready content for each changed file, not vague fragments.
6. After each milestone, tell me exactly how to run it and what output I should expect. Wait for me to report the result before moving to the next milestone.
7. Use Python 3.11-compatible, maintained libraries. Avoid unnecessary dependencies.
8. Never hardcode API keys, tokens, passwords, or other secrets. Use `.env`, provide `.env.example`, and make sure `.env` is in `.gitignore`.
9. Do not pretend that mock/sample listings are live data. Clearly label test fixtures and fallbacks.
10. Do not invent opportunities, URLs, deadlines, eligibility rules, or API behavior. Cite/source-link real results and handle missing data gracefully.
11. Add basic validation and useful error messages. Add focused tests for ranking/filtering logic.
12. Keep the architecture understandable to a beginner. Explain important design decisions in plain English.
13. Do not claim that Vison is registered, deployed, ACP-compatible, or visible in ASI:One until it has actually been tested and verified.
14. Before implementing Fetch.ai/uAgents/ASI:One integration, consult the current official documentation and challenge rules. Use supported APIs/protocols; do not invent SDK methods or endpoint names.
15. Keep a running checklist of completed and remaining challenge requirements. Separate verified requirements from assumptions.
16. Never ask me to paste secrets into chat. If a secret is needed, explain how I can put it in my local `.env` file.

### Milestones
- **Milestone 1 — Local MVP:** Create a small command-line program that accepts a sample/user profile and returns ranked opportunities. Start with test/sample data if no live source is yet configured, label it clearly, and keep the source layer replaceable.
- **Milestone 2 — Reliable data source:** Identify a suitable, accessible source/API for real hackathons and internships. Check terms, authentication needs, rate limits, and data quality. Implement one source first and preserve source URLs and dates.
- **Milestone 3 — Matching quality:** Add explainable scoring, eligibility filters, missing-field handling, and tests. Do not reject users based on assumptions.
- **Milestone 4 — Agent integration:** Integrate the current official Fetch.ai/uAgents and required ASI:One/ACP workflow according to the hackathon rules and documentation.
- **Milestone 5 — Platform deployment:** Configure and test deployment/registration on the required platform. Give me the exact steps and verify each one.
- **Milestone 6 — Submission package:** Prepare README, `.env.example`, requirements, tests, public GitHub setup, required platform/chat URLs, and a 3–5 minute demo script if the challenge requires them.

### Start now
Begin with **Milestone 1 only**. First tell me how to confirm the current folder and inspect existing files using PowerShell. Then propose the minimum files for the first working version and provide the code and run commands. Do not jump to deployment before the local version works. Ask me to share any terminal output or errors and troubleshoot them one at a time.

## 7. Useful prompts for later milestones

### Debug an error
```text
Help me debug this Vison AI error. First explain what the error means in plain English. Identify the likely cause, ask for any missing relevant file/output, then give the smallest safe fix. Do not rewrite unrelated files. Tell me the exact command to retest.
Error:
[PASTE ERROR HERE]
```

### Add a feature
```text
Add this feature to Vison AI: [DESCRIBE FEATURE].
First explain the design and list the files that need to change. Keep the change small, compatible with Python 3.11, and covered by a focused test. Do not break the current working flow. Give exact run/test commands.
```

### Review for the hackathon
```text
Review Vison AI against the current official Fetch-A-Thon 3.0 — ASI:One Agent Challenge requirements. Verify current requirements from official sources, then make a table of requirement, evidence in the repo/platform, status (verified / incomplete / unknown), and next action. Do not mark anything complete without evidence.
```

### Prepare demo
```text
Help me prepare a truthful 3–5 minute Vison AI demo. Base it on the features that actually work in the repository. Provide a timed script, exact commands/clicks, expected outputs, and a short explanation of the agent's value. Do not show fake live results or claim unverified deployment.
```

## 8. Team collaboration

For a team of 2:
- Person A: main app, integration, final decisions.
- Person B: opportunity-source research, test cases, README/demo support.

For a team of 3–4:
- Person A: main agent and integration.
- Person B: data source research and implementation.
- Person C: matching/ranking and tests.
- Person D: deployment, documentation, demo, and requirement verification.

Use one shared GitHub repository. Agree on file ownership and avoid editing the same file simultaneously. Keep API keys and `.env` files out of Git.

## 9. Definition of done

Vison is not done just because it starts. Before submission, verify:
- [ ] A user can complete the intended workflow from input to useful results.
- [ ] Results are real and source-linked, or clearly labelled as sample data.
- [ ] Ranking reasons and missing data are understandable.
- [ ] Important logic has tests.
- [ ] Setup works from a clean environment using the README.
- [ ] Secrets are not committed.
- [ ] Required agent protocol and platform workflow are tested.
- [ ] Required submission links and demo are ready.
- [ ] Every competition requirement has evidence or is clearly marked incomplete.

**Instruction to the AI:** Keep me moving one step at a time. Do not dump the whole implementation at once. Make the next step easy to execute, verify, and debug.
