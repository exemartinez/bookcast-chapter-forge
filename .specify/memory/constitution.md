# bookcast-chapter-forge Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Object Oriented programming First - Make it all object oriented programming and modular.
Every feature should be thought in a way its implementation comes as an OO first project.
Define classes, data classes and transfer objects instead of vainilla objects.
Stablish entities before you deep dive into the procedures.
Respect interfaces and its due contracts.
Every feature starts as a standalone library/module; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries.
Every non-trivial class must start with a short commentary or docstring that explains its purpose, what it achieves, and why it exists.
Every non-trivial method must start with a short commentary or docstring that explains its purpose, what it achieves, and why it exists.
Trivial classes and trivial methods are the only exception to this rule.

### II. CLI interface
Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats

### III. Test-First (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced. Mock and Stub functionality that isn't present; respect interfaces. 
Tests must not require mutating valid user data files or valid user configuration files just to pass.
Refactors and bugfixes must adapt code or test-owned fixtures, not repository user inputs, unless the data or configuration is objectively invalid by definition.
Any integration or end-to-end test that depends on large real-world inputs or takes noticeable time must be explicitly marked as a slow test.
Default test runs must remain fast; slow tests should run only when explicitly requested.

### V. Observability
Structured logging required

### VI. Versioning & Breaking Changes,
Do not refactor if the class or method doesn't has test coverage.

### VII. Simplicity 
Start simple: YAGNI -> KISS -> DRY principles. Maintain versioning: MAJOR.MINOR.BUILD format; 

## Technology stack
Python 3.9+ plus libraries.

## Governance
Constitution supersedes all other practices; Amendments require documentation, approval, migration plan.

## Additional Standards (Additive)

### VIII. Strategy Isolation and Additive Evolution
New chapter-detection capabilities must be introduced as additive classifier strategies that implement existing interfaces.
Strategy-specific optional dependencies must be isolated so missing packages do not break unrelated strategies.
No feature may force global architectural rewrites when the same goal can be achieved through a new classifier module.

### IX. Contract and Data Integrity
Every classifier must return contract-valid `ClassificationResult` values:
- chunk ranges must be ordered and non-overlapping
- chunk ranges must stay within document page bounds
- zero-length chunks are forbidden
When confidence is low, classifiers should emit clear warnings/metadata rather than silently returning misleading boundaries.

### X. Reproducibility and Determinism
Boundary decisions must be deterministic by default for the same input and configuration.
When heuristics include tie-breakers, tie-break rules must be explicit and documented in code-level comments or module docs.
Experimental model-assisted modes must remain optional and must not degrade deterministic non-model strategies.

### XI. Configuration and Dependency Discipline
Runtime behavior must be configuration-driven; hardcoded strategy behavior should be avoided except for safe defaults.
Optional integrations must have graceful import/runtime failure paths with actionable error messages.
The baseline installation path must continue to support existing workflows without requiring optional heavy dependencies.
Imports must be declared at module top-level. Inline function/method imports are disallowed except in narrowly documented circular-import workarounds approved in the feature plan.

### XII. Security and Privacy for Model-Assisted Flows
No external network model dependency may be introduced by default.
If model-assisted logic is used, it should process structured candidate evidence instead of raw full-document dumps when possible.
Logs must avoid leaking full sensitive document text unless explicit debug mode is enabled by the user.

### XIII. Documentation and Spec Traceability
Each feature must maintain traceability: `spec.md` -> `plan.md` -> `tasks.md` -> implementation/tests.
Closure notes should record what landed, known limitations, and what remains intentionally out of scope.
README and strategy documentation must state "best-effort" limitations clearly when chapter extraction is heuristic.

**Version**: 1.4.1 | **Ratified**: 2026-04-03 | **Last Amended**: 2026-04-08
