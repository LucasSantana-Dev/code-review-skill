# ADR-0025: Monetization path — defer; keep the core free + open; upside is operator expertise, not a paywall

- **Status:** Accepted (decision = **defer active monetization**, with demand-gated triggers)
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Extends:** [ADR-0005](0005-curated-knowledge-not-autonomous-learning.md) (open forkable knowledge layer = the wedge), [ADR-0008](0008-permissive-not-copyleft-for-the-corpus.md) (Apache-2.0 core), [ADR-0010](0010-headless-ci-action-runner.md) (no hosted infra; wedge = the open layer)
- **Informed by:** `/research-and-decide` — 5 parallel web-grounded research angles + an adversarial `critic` (verdict: REVISE), 2026-06-06

## Context

Question raised: *is there room to grow from a free solution to something profitable
eventually?* Research surveyed how comparable tools monetize (CodeRabbit, Qodo/PR-Agent,
Greptile, Graphite [acquired by Cursor], Cubic, Sourcegraph, Copilot review) and how
permissive-core OSS monetizes (Sentry/FSL, HashiCorp→OpenTofu, Redis→Valkey, n8n,
Tailwind, sponsorware). The product is a solo-operated, Apache-2.0, self-hostable,
BYO-LLM/Ollama code reviewer whose **differentiator is the open, forkable, curated
`references/` knowledge layer + calibration discipline** — explicitly *not* AI-quality
parity (commoditized by frontier LLMs). A locked decision (ADR-0010) avoids hosted/
multi-tenant infrastructure.

The adversarial critic refuted the appealing "yes, go monetize now" framing on five
load-bearing points (ranked by severity):
1. **A sponsors-only/premium `references+` pack cannibalizes the wedge** — it paywalls the
   very thing ADR-0005/0010 lock as *open and forkable*, and under Apache-2.0 it is
   **unenforceable** (fork the public commit). Self-cancelling.
2. **A fixed-price support SLA is unsustainable solo** — "org-specific reference tuning +
   48h response" is ~5–8 hrs per novel pattern; the SLA becomes a churn/burnout trap, not
   margin.
3. **SOC2 + regulated/self-host "enterprise" wedge is a mirage on spec** — ~$30–50k upfront
   + $10–15k/yr ongoing + a full-time enterprise sales motion a no-brand solo op cannot run;
   incumbents already serve that segment.
4. **Sponsorship ≠ passive revenue** — ~90% of sponsors come from an existing audience the
   operator does not yet have; the tool is also trivially forkable + Ollama-runnable (free-rider).
5. **It is premature** — the CI Action hasn't shipped; a Claude-Code-only skill isn't yet
   adoptable by teams, so there is nothing to monetize and no usage signal to price against.

## Decision

**Defer active monetization. Keep the core free, open, and Apache-2.0 — that openness *is*
the differentiator and must not be paywalled.** Pursue revenue only along a sequenced,
demand-gated path that preserves every locked constraint:

1. **Ship and prove the product first.** No monetization move before the CI Action runner
   (Phases 0–2, [roadmap](../docs/roadmap.md)) ships and earns **real usage data**. Usage is
   the prerequisite, not an afterthought.
2. **Then a no-strings "support development" tip-jar** (GitHub Sponsors / Open Collective),
   framed as *supporting the maintainer* — **not** premium features, **not** an SLA. Expected
   modest (offset, not a business); never gate any `references/` content behind it.
3. **The genuine upside lever is the operator's expertise, sold per-engagement** — paid
   code-review audits / setup / org-specific tuning / training, with the tool as a free
   credential and loss-leader. Per-engagement (or per-incident) pricing — **never** a
   fixed-price support SLA. This is controllable, high-margin, and breaks no constraint.
4. **Everything heavier stays deferred behind explicit demand triggers** (below) and is
   **never built on spec**: the regulated/self-host + SOC2 enterprise wedge; an optional
   hosted tier (would break ADR-0010); and FSL/source-available licensing — which, if ever
   used, applies **only to genuinely new premium modules**, never the shipped Apache-2.0 core
   or the open `references/` layer.

Honest ceiling, stated plainly: this is a **modest solo upside / portfolio-and-loss-leader
with an expertise-led revenue option**, *not* a venture-scale or even reliably mid-four-figure
SaaS business. Treat it as such.

## Alternatives considered

- **Sponsors-only / premium `references+` pack (sponsorware)** — rejected: cannibalizes the
  open-layer wedge (ADR-0005/0010) and is unenforceable under Apache-2.0.
- **Fixed-price support / curation SLA ($800–2,500/mo)** — rejected as a *product*: the unit
  economics don't pencil for a solo op and the SLA invites churn/burnout. Re-expressed as
  per-engagement consulting instead.
- **SOC2 + regulated/self-host enterprise tier, built on spec** — rejected now: ~$70–100k
  sunk-cost risk + full-time sales a solo op can't staff; demand-gate it instead.
- **Hosted multi-tenant SaaS** — rejected: reintroduces exactly the infra/ops burden ADR-0010
  deliberately avoided; only reconsider on unambiguous inbound + existing revenue + capacity.
- **Relicense the core to BSL/SSPL to force payment** — rejected: irrevocable for shipped
  Apache-2.0 code, and the trust/fork damage is well-precedented (HashiCorp→OpenTofu,
  Redis→Valkey); also violates ADR-0008.
- **FSL/source-available on future premium modules** — deferred, not adopted: viable only if a
  genuinely-new, separable premium module exists and demand is proven; not the core, not `references/`.

## Consequences

**Positive:** preserves the differentiator and community trust (the open layer stays open);
zero new infra and zero burnout risk (no SLA, no hosting); honest expectations prevent a
demand-blind rebuild; the expertise/consulting lever is controllable, high-margin, and
constraint-safe; all heavier bets are option-valued behind real signals.

**Negative:** the realistic revenue ceiling is modest and **gated on an audience/reputation
the operator has not yet built**; the expertise path trades time-for-money (non-scalable);
"defer" means no near-term revenue and a real chance the honest answer stays "free
portfolio/loss-leader."

**Neutral:** the product, license, and architecture are unchanged by this decision — it is a
*business-model* decision (defer + gate), not a code or positioning change.

## Revisit when (demand triggers — none are assumed; instrument for them)

- **CI Action ships and gets real traction** — e.g. **≥30 repos / ≥100 installs** using it
  within ~2 months → turn on the no-strings tip-jar with real usage to point at.
- **Unsolicited willingness-to-pay appears** — e.g. **≥5 inbound requests in a quarter** asking
  to pay, for paid support, or for help setting it up → formalize per-engagement consulting.
- **A paid audit/consulting engagement closes** (≥1 external team pays for review expertise) →
  validates the expertise lever; lean into it.
- **A genuine regulated-buyer conversation with confirmed budget appears** (real email/Slack,
  not hypothesis) — **≥5 in a quarter** → only then evaluate SOC2 + a self-host support tier,
  and validate willingness-to-pay *before* spending on compliance.
- **The operator builds audience/reputation** (a post/talk with real reach in the code-review
  space) → sponsorship conversion becomes realistic; revisit the tip-jar's expected value.
- **Abort/"""keep-it-free""" signal:** if, ~6 months after the Action ships, none of the above
  fire → accept "free portfolio + loss-leader" as the answer and stop spending effort on monetization.
