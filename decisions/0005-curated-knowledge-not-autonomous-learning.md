# ADR-0005: Compounding review quality via a curated knowledge layer, not an autonomous learning loop

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Lucas Santana (solo operator)
- **Supersedes:** (none — extends ADR-0002's calibration with the surrounding "what makes this better" thesis)
- **Superseded by:**

## Context

The skill's north star is "not a linter/SAST — real reviews that catch what those miss," and the
stated aspiration is that it "learns patterns from each review to deepen its examples, references,
and performance" — a free, open-source, customizable "CodeRabbit but better." This forced a
decision about the **architecture of the differentiator**: how does the skill get *better over
time*, and what feeds that?

Constraints that bound the answer:
- Packaged as an Agent Skill (SKILL.md + bundled Python-stdlib scripts); "free" = inference runs
  in whoever's own agent (BYO compute), no hosted service (ADR-0003).
- Operator is a **solo developer, ~5 active repos, low PR volume** (handful/week, not 50+/week).
- The skill is **stateless today** — zero persistence; SKILL.md memory hooks are advisory only.
- Existing reusable infra: a local RAG index (`~/.claude/rag-index`, incremental, hybrid
  BM25+cosine+RRF+rerank) and the `knowledge-loop`/`recall`/`sync-memories`/`rag-curate` skills.

Research (4 parallel strands) + an adversarial critic established:
- Tools that "learn" (CodeRabbit learnings DB, Greptile vote-embeddings, Cursor BugBot
  experimentation) do it with persistent feedback infra and, crucially, **at volume**. The
  open-source ones (PR-Agent et al.) are stateless, diff-only.
- Learning **requires a validation signal** or it degrades (model collapse from training on its own
  unvalidated output).
- **Null hypothesis is well-supported:** a great static rubric + curated version-controlled
  references + full-repo context captures ~70–80% of the value *today*; an autonomous learning loop
  adds ~5–15% **only at high PR volume**. At low volume, feedback is too sparse to compound.
- Best value×LLM-feasibility defect classes: semantic bugs, business-logic correctness,
  intent-vs-implementation mismatch (Tier 1); cross-file invariants, API/exception misuse,
  architecture (Tier 2); concurrency & security-logic are high false-positive (flag, never approve).

## Decision

Achieve compounding review quality through a **curated knowledge layer with a human in the loop**,
**not** an autonomous self-training loop. Concretely:

1. **Encode the defect taxonomy into the rubric.** Make Tier-1 classes (semantic bugs,
   business-logic correctness, intent-vs-impl mismatch) the primary lens; Tier-2 secondary; mark
   concurrency & security-logic as *flag-don't-approve* (high FP). This is what makes it a "real
   review," not lint.

2. **Ship a generalizable, forkable references library *with the skill*.** A version-controlled set
   of defect patterns + good/bad examples (the kind that transfer within a language/framework).
   This open, customizable corpus — not raw model intelligence — is the product shape that
   distinguishes a free/open tool from a proprietary locked learnings DB.

3. **Reuse each target repo's own convention docs for repo-specific knowledge.** Repo-specific
   patterns don't transfer and must NOT live in the skill repo; the skill already reads the target
   repo's `CLAUDE.md`/`AGENTS.md`/ADRs (context-first). No new per-repo maintenance burden.

4. **"Learning" = curation.** When a review surfaces a novel *generalizable* pattern, a human
   adds/refines a reference (a curation step in the release checklist). Compounds at any volume,
   fully auditable, no collapse risk.

5. **Defer the autonomous validation loop** (RAG retrieval of past validated findings + PR-outcome
   signal + auto-promotion). It is recorded here as a designed-but-deferred option, not built now.

## Alternatives considered

- **Autonomous learning loop now (RAG + PR-outcome validation, auto-promote findings).** Rejected
  *for now*: ROI is upside-down at solo/low-volume (≈5–15% upside vs. ~24 hrs/yr cost), and
  "proposes, human disposes" at low volume is manual curation with extra machinery. Deferred behind
  explicit triggers (see *Revisit when*).
- **Fine-tuning / DPO on a review corpus.** Rejected: needs 1k–10k labels, model lock-in, fights
  free/open/customizable; no plausible label volume.
- **Pure static prompt, no references library.** Rejected: leaves the open/forkable/customizable
  differentiator on the table; references are what let findings cite a durable rationale.
- **In-review multi-pass reflection as the differentiator.** Kept as a *complementary* technique
  (cheap precision lift), not the architecture; it doesn't compound across reviews.
- **Differentiate on full-repo context depth.** Real but not exclusive; the existing RAG index
  already supplies repo context. Folded in, not chosen as the headline.

## Consequences

**Positive:**
- Ships now with no new persistence machinery; no model-collapse surface.
- Compounds at the operator's actual volume (human curation works at any cadence).
- The references library is the open, forkable artifact that makes "free + open + customizable"
  concrete — genuinely different from proprietary tools' locked learnings.
- Honest expectations: we call it curation, not "self-learning AI."

**Negative:**
- Curation is manual labor; if the operator stops curating, the library stagnates (mitigation:
  make a reference-curation check part of the release checklist).
- We forgo the ~5–15% that an autonomous loop *might* add at volume — accepted until volume exists.

**Neutral:**
- The validation-signal design (hunk-changed-before-merge as a *weak prior* + explicit 👍/👎 +
  dismissed→never-store) is specified now so Layer 2 can be built quickly if a trigger fires.

## Pilot / rollout

- **Pilot (next ~10 real reviews):** run with the curated layer only. Track per finding: did a
  reference catch something the operator would have missed? and the dismiss/false-positive rate.
- **Success criteria:** references measurably surface ≥1 real issue the operator would have missed
  across the pilot, and dismiss rate stays low. If "meh, I catch most things anyway" → keep the
  library lean and do NOT build Layer 2.
- **Rollback:** the layer is just markdown + rubric text; revert is deleting/trimming files. No
  data migration, no service to tear down.

## Revisit when

- Sustained PR volume rises above ~20–30/week, **or** a second contributor joins (feedback density
  crosses the threshold where an autonomous loop compounds).
- The pilot shows the curated library has saturated (operator keeps hitting patterns the static
  library should have surfaced but didn't) **and** volume justifies automation.
- An explicit 👍/👎 capture path becomes cheap to wire (moves validation fidelity from ~75% to
  ~95%), lowering Layer 2's risk enough to reconsider earlier.

## References

- Research strands (2026-06-06): competitive landscape; learning-mechanism design; codebase/
  ecosystem grounding; defect taxonomy + null hypothesis.
- Critic verdict (2026-06-06): PROCEED-WITH-CHANGES — build curated layer now, defer the loop,
  reframe "learning" as "curation," don't drop the explicit-feedback signal.
- Related: ADR-0002 (confidence calibration), ADR-0003 (skill packaging), ADR-0004 (posting identity).
