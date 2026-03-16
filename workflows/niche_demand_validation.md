# Workflow: Niche Demand Validation Research

## Objective

Determine whether a consulting or content niche has real, documented demand — and whether a solo practitioner can realistically access that demand. Return a go/no-go signal with sourced evidence, not just market statistics.

## When to Use This

Before committing to a positioning, YouTube series, or consulting offering. This workflow answers:
- Is the pain real and felt, or just theoretically plausible?
- Are companies already spending money on this (job postings, funded tools)?
- Is the niche owned, underpopulated, or overcrowded?
- Where do the buyers actually spend time?

---

## Inputs Required

- **Proposed niche** (one sentence): e.g., "PII-safe AI automation for mid-market regulated industries"
- **Target buyer** (role + company type): e.g., "IT Directors at 500-5000 employee healthcare orgs"
- **Practitioner background**: what credentials and experience the consultant brings
- **Known alternatives**: tools or firms already serving this space (even partially)

---

## Step 1: Find the Felt Pain

**Goal:** Find people complaining about this problem in their own words — not analyst reports saying the problem exists.

**Where to look:**
1. Hacker News — search `site:news.ycombinator.com "[pain keyword]"` on Google; look for threads with 100+ comments
2. Reddit — r/dataengineering, r/devops, r/healthIT, r/sysadmin, r/cscareerquestions depending on domain
3. LinkedIn comments/posts — search for the pain keyword + "we can't" or "legal said no" or "compliance blocked"
4. OpenAI/Anthropic/Hugging Face community forums — practitioners trying to solve the exact problem
5. Product launch threads (Show HN, Product Hunt) — read the comments, not the pitch; frustrated comments confirm pain

**What counts as signal:**
- Direct quotes from practitioners describing the blocker
- "We got burned" stories — past incidents that created the policy
- Repeated questions about the same problem across multiple threads
- Companies named as examples of the failure (Samsung, etc.)

**What does NOT count:**
- Analyst reports saying "X% of companies face this challenge"
- Vendor blog posts describing the problem they solve
- Generic LinkedIn thought leadership posts

**Output:** 3-5 concrete quotes or incidents with source URLs.

---

## Step 2: Find the Spending Signal

**Goal:** Confirm companies are already paying money to solve this — even imperfectly.

**Method A: Job postings as proxy**
Job postings reveal what companies will write a check for. Search LinkedIn Jobs and Indeed with combinations of:
- Domain keyword (healthcare, FedRAMP, HIPAA) + technical skill (data migration, data engineer) + new capability (AI, LLM, automation)
- Note: count of results matters less than *who* is posting. Big 4 posting 30+ roles = market is real but enterprise-skewed.

**What to record per posting:**
- Job title + company + salary range
- 2-3 key requirements that confirm the intersection you're targeting
- URL (postings expire — archive important ones)

**Method B: Funded product companies**
If VCs are funding companies solving adjacent problems, the market is real. Search:
- `site:techcrunch.com [niche keyword]`
- `site:ycombinator.com/companies [niche keyword]`
- Crunchbase for companies in the space

Record: company name, funding amount/stage, customer wins if public, pricing tier. Note which layer they solve and what they leave unaddressed — that's your gap.

**Method C: Pricing signals**
What are buyers paying for solutions today? This anchors your pricing conversation.
- Product pricing pages (SaaS tiers)
- Glassdoor/LinkedIn salary data for in-house roles doing this work
- Catalant/Toptal project postings if visible

**Output:** Table of job postings + funded tools with sources.

---

## Step 3: Map the Competitive Landscape

**Goal:** Determine if the niche is owned, underpopulated, or overcrowded — at the *individual practitioner* level, not the enterprise firm level.

**Check each tier:**
1. **YouTube channels** — search YouTube directly. Are there channels with 10K+ subscribers specifically targeting this intersection? If yes, note their approach and differentiation opportunity. If no, that's a gap.
2. **Solo consultant brands** — Google `[niche] consultant` and look for individual practitioner websites, not firms. LinkedIn search for people with this positioning in their headline.
3. **Newsletters/communities** — Substack search, beehiiv, LinkedIn newsletters. Is anyone publishing specifically on this intersection?
4. **Mid-tier firms (not Big 4)** — boutiques and staffing firms (ICF, Milliman, etc.) that serve the mid-market. These are potential subcontracting paths, not just competitors.

**Key distinction:** Big 4 presence in a niche is *bullish*, not threatening. It validates the market while confirming the enterprise tier is locked up — which means mid-market is available.

**Output:** Gap statement — who owns what tier, and where the opening is.

---

## Step 4: Find the Watering Holes

**Goal:** Know exactly where to reach the buyer before you have a network.

**For each buyer persona:**
- What professional associations do they belong to? (HIMSS for healthcare CIOs, ACT-IAC for federal IT)
- What newsletters/publications do they read? (FedScoop, Data Engineering Weekly, etc.)
- What Reddit communities do they participate in?
- What LinkedIn groups are active vs. zombie?
- What conferences do they attend?

This becomes the distribution plan for content and outreach.

**Output:** List of 5-8 specific, named channels with estimated audience size where possible.

---

## Step 5: Honest Go/No-Go Assessment

Rate each signal:

| Signal | Strong | Moderate | Weak | Absent |
|--------|--------|----------|------|--------|
| Felt pain (practitioner complaints) | | | | |
| Job postings (spending proxy) | | | | |
| Funded products (VC validation) | | | | |
| Mid-market buying from solo/boutique | | | | |
| Niche unowned at solo level | | | | |
| Clear watering holes to reach buyer | | | | |

**Go** if: felt pain is strong + at least 2 other signals are strong/moderate, niche is unowned at solo level.

**Conditional go** if: pain is real but mid-market buying behavior is weak — means subcontracting path (Umbrex, staffing firms) is required before direct-client sales.

**No-go** if: pain exists only in theory (no actual complaints found), OR niche is already owned by established solo practitioners with strong content presence.

---

## What This Workflow Does NOT Answer

- Whether *you specifically* can win in this niche (that's a skills/credibility assessment)
- Whether the niche has good unit economics (that's a pricing/market-size calculation)
- Whether the buyer finds you (that's a go-to-market plan)

Run those as separate analyses once you have a go signal here.

---

## How This Workflow Was Built

This workflow was developed iteratively through a real demand validation session. The methodology reflects what actually worked:

**What the user asked for that shaped this:**
- "I don't want broad statistics, I want proof that this is a headache area for people" → Step 1 focuses on felt pain, not analyst data
- "I want to know how much demand" → Step 2 uses job postings as a spending proxy, not TAM calculations
- "It's harder for me to imagine how many midsized companies are willing to take a chance on a solo agency" → Step 5 explicitly separates "demand is real" from "solo practitioners can access it"

**Points that were pushed on (uncertainty the user surfaced):**
- "Does hiring a consultant justify the cost over out-of-the-box tools?" → The honest answer: you don't compete with tools, you wield them. The real alternative is the client's internal team trying to DIY it.
- "How does Presidio guarantee 100% PII detection?" → It doesn't. The value is layered defense + offramp architecture = defensible auditable risk reduction, not perfection.
- "I don't have a network — I've only worked on government contracts" → Reshaped path from direct-client-first to subcontracting-first (Umbrex) + content-first inbound.

**Things that landed well:**
- The offramp concept (human-in-the-loop routing for low-confidence detections) resonated immediately as both a technical solution and a YouTube video concept
- Framing the niche as "compliant agentic AI for regulated data" — intersection of migration expertise + PII architecture + FedRAMP literacy
- Big 4 posting 30+ roles = validating signal, not threatening signal

**Lessons for future validation runs:**
- Hacker News comment threads are more valuable than news articles for felt pain
- Job postings reveal both real demand and who owns which market tier
- Funded product companies confirm the market while revealing which layer remains unaddressed by tools — that's the consulting wedge
- "No solo consultant owns this" is itself a demand signal, not just an absence of data
