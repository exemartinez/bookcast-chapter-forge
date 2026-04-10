# - FOR HUMAN EYES ONLY -
# Purpose

This document defines the standard development lifecycle for this repository.

It is designed to ensure:
- Deterministic feature delivery
- Traceability from idea → implementation
- High-quality, testable outputs
- Reproducibility across contributors

This is not optional guidance. It is the operating model.

---

# Core Principles
1. Specification-first development. No implementation begins without a defined spec.md.
2. Separation of concerns
- What → spec.md
- How → plan.md
- Execution → tasks.md
- Reality → code
3. Scaffolding over automation Spec-Kit accelerates structure, not thinking.
4. Human-in-the-loop engineering. All critical decisions (architecture, trade-offs, validation) are manual.
5. Test against reality, not assumptions. Real PDFs are the source of truth—not mocks alone.

---

# End-to-End Workflow

#### Phase 1 — Feature Definition
1. Create feature scaffold, for example: 
```
.specify/scripts/bash/create-new-feature.sh --json --short-name "heuristic-chapter-detection" "Heuristic PDF chapter detection that improves on feature 001 by evaluating multiple structural signals such as TOC text, page labels, hyperlinks, PDF outlines, layout-aware heading extraction, and optional local-model assistance to choose chapter boundaries more reliably across messy English-language books"
```
2. Write spec.md

Output
- Clear, testable definition of the feature

Exit Criteria
- No ambiguity in expected behavior
- Edge cases explicitly stated

---

#### Phase 2 — Planning
3. Generate plan scaffold
```
.specify/scripts/bash/setup-plan.sh --json
```
4. Fill plan.md

Output
- Concrete implementation strategy

Requirements
- Architecture decisions documented
- Dependencies identified
- Risks explicitly stated

Exit Criteria
- Another engineer could implement from this document

---

#### Phase 3 — Task Decomposition
5. Generate and refine tasks.md, first run:
```
.specify/scripts/bash/check-prerequisites.sh --json
```
- Pre-implementation: update `agents` (we used `codex`, but any `agent` will do.)
```
.specify/scripts/bash/update-agent-context.sh codex
```
- Check prerrequisites:
```
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```
6. Ask the LLM agent to generate your `tasks.md` file based on `plan.md` and `spec.md`, then fulfill its template requirements. 

Output
- Atomic, ordered execution steps

Requirements
- Tasks must be:
- Small (≤ 1–2 hours each ideally)
- Testable
- Independently completable

Exit Criteria
- No ambiguity in execution
- Clear completion criteria per task

---

#### Phase 4 — Implementation
7. Implement strictly following tasks.md

- Run implementation (ask the LLM to do it - Cursor, Pycharm, Claude Code, etc.)

Rules
- Do not improvise outside tasks without updating tasks.md
- Mark tasks as completed immediately after execution
- Keep commits aligned with task boundaries

Exit Criteria
- All tasks completed
- No skipped steps

---

#### Phase 5 — Validation
7. Run tests
```
./bookcast-ve/bin/pytest
```
8. Manualy validate against real PDFs (`slow` testing)

Requirements
- Unit tests & Slow tests must pass
- Functional validation must match real-world behavior

Exit Criteria
- No regressions
- Output matches spec

---

# Command Reference

All commands are executed from the repository `root`.

## Feature Creation

```
.specify/scripts/bash/create-new-feature.sh \
  --json \
  --short-name "pdf-chapter-classifier" \
  "PDF reader/parser with ChapterClassifier-based chapter chunking"
```

---

## Plan Setup
```
.specify/scripts/bash/setup-plan.sh --json
```

---

## Prerequisite Checks (Pre-Tasks)

```
.specify/scripts/bash/check-prerequisites.sh --json
```

---

## Agent Context Update

```
.specify/scripts/bash/update-agent-context.sh codex
```

---

## Prerequisite Checks (Pre-Implementation)

```
.specify/scripts/bash/check-prerequisites.sh \
  --json \
  --require-tasks \
  --include-tasks
```


---

## Run Tests

```
./bookcast-ve/bin/pytest
```

---

## Run CLI

```
PYTHONPATH=src \
./bookcast-ve/bin/python \
src/bookcast_chapter_forge/cli/pdf_parser.py --help
```

---

# Responsibility Model

## Automatic (Spec-Kit)
- Generates feature scaffold
- Generates initial plan.md
- Updates AGENTS.md
- Provides prerequisite diagnostics

## Manual (Engineer)
- Define spec.md
- Complete plan.md
- Create/refine tasks.md
- Implement all code
- Execute and validate tests
- Maintain task state

---

# Engineering Invariants

These are non-negotiable:
- Spec.md must exist before plan.md
- Plan.md must exist before tasks.md
- Tasks.md must exist before implementation
- Implementation must map 1:1 to tasks
- No “hidden work” outside tracked tasks
- Tests must validate real behavior, not only mocked paths

---

# File Semantics

## spec.md

Defines:
- Functional behavior
- Inputs / outputs
- Edge cases
- Constraints

Anti-patterns
- Implementation details
- Vague language

---

## plan.md

Defines:
- Architecture
- Data flow
- Dependencies
- Trade-offs

Anti-patterns
- Task-level granularity
- Hand-wavy decisions

---

## tasks.md

Defines:
- Step-by-step execution

Anti-patterns
- Large tasks
- Ambiguous outcomes

---

# Mental Model

We think in layers:

```
spec → plan → tasks → code → validation
```

Or more explicitly:
- spec.md = intent
- plan.md = strategy
- tasks.md = execution
- code = artifact
- tests = truth

---

# Quality Bar

A feature is considered complete only if:
- All tasks are marked complete
- Tests pass consistently
- Behavior matches spec.md
- Real-world validation is successful
- No implicit assumptions remain
---

# Common Failure Modes

Avoid these:
- Skipping spec.md → leads to rework
- Overloading plan.md with tasks → breaks abstraction
- Large tasks → poor traceability
- Implementing outside tasks.md → loss of control
- Testing only with mocks → false confidence

---

# Extension Guidelines

When evolving this workflow:
- Do not collapse phases
- Do not merge files (spec, plan, tasks)
- Prefer adding constraints over removing structure
- Maintain traceability at all costs

---

# Optional Enhancements (Future)
- CI enforcement:
- Block PRs without tasks.md completion
- Task → commit mapping automation
- Spec completeness linting
- Real-data validation pipelines

---

This document should be treated as a living operational contract. Any deviation must be explicit and justified.

**Version**: 1.0.0 | **Ratified**: 2026-04-08 | **Last Amended**: 2026-04-08
