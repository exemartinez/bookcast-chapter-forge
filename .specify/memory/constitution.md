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

**Version**: 1.3.0 | **Ratified**: 2026-04-03 | **Last Amended**: 2026-04-07
