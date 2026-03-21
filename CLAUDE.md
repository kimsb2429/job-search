# Agent Instructions

You're working inside the **SWAT framework** (Skills, Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The SWAT Architecture

**Layer 1a: Skills (Simple Actions)**
- Markdown SOPs stored in `~/.claude/skills/`
- Self-contained, single-purpose actions (e.g., `/capture`, `/closetabs`, `/wrapup`)
- Invoked via `/skill-name` slash commands

**Layer 1b: Workflows (Multi-Step Pipelines)**
- Markdown SOPs stored in `workflows/` in this repo
- Complex pipelines involving multiple tools, defined inputs/outputs, and edge case handling
- Follow the structured template: Objective, Inputs, Steps, Outputs, Edge Cases, Rate Limits/Constraints
- Invoked by asking Claude (e.g., "run the job application workflow")

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant skill, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

**Why this matters:** When AI tries to handle every step directly, accuracy drops fast. If each step is 90% accurate, you're down to 59% success after just five steps. By offloading execution to deterministic scripts, you stay focused on orchestration and decision-making where you excel.

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your skill requires. Only create new scripts when nothing exists for that task.

**2. Learn and adapt when things fail**
When you hit an error:
- Read the full error message and trace
- Fix the script and retest (if it uses paid API calls or credits, check with me before running again)
- Document what you learned in the skill (rate limits, timing quirks, unexpected behavior)

**3. Keep skills current**
Skills should evolve as you learn. When you find better methods, discover constraints, or encounter recurring issues, update the skill. That said, don't create or overwrite skills without asking unless I explicitly tell you to. These are your instructions and need to be preserved and refined, not tossed after one use.

## The Self-Improvement Loop

Every failure is a chance to make the system stronger:
1. Identify what broke
2. Fix the tool
3. Verify the fix works
4. Update the skill with the new approach
5. Move on with a more robust system

This loop is how the framework improves over time.

## File Structure

**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Multi-step pipeline SOPs (structured template)
notes/inbox/    # Quick captures via /capture skill
TODO.md         # Active task list
.env            # API keys and environment variables (NEVER store secrets anywhere else)
credentials.json, token.json  # Google OAuth (gitignored)
```

**Core principle:** Local files are just for processing. Anything I need to see or use lives in cloud services. Everything in `.tmp/` is disposable.

## Before Expanding Auto-Apply

Before adding any new auto-apply channel, research whether a legitimate API exists:
- Check if the job board has a public candidate-facing apply API (rare — most boards have intentionally closed these)
- Check GitHub for open-source solutions and their approach (API vs browser automation)
- Document what you find: which boards have APIs, which require browser automation, and what the CAPTCHA/ToS risks are
- Present findings before building — do not assume browser automation is the right path without confirming no API exists

**Known apply channels (as of March 2026):**
- ClearanceJobs `email`-method: API-based (implemented in `tools/auto_apply.py`)
- LinkedIn / Indeed / ZipRecruiter: No public apply API — browser automation only (fragile, ToS risk)
- Greenhouse ATS: Has API but requires per-company private key (not practical for bulk)

## Bottom Line

You sit between what I want (skills + workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

Stay pragmatic. Stay reliable. Keep learning.
