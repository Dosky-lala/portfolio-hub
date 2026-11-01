# Postmortem: Validation regression blocked at pull request (near miss)

| | |
|---|---|
| **Date** | 2026-11-01 |
| **Severity** | SEV-4 / near miss (no user impact) |
| **Status** | Resolved |
| **Type** | Planned break-it drill |

## Summary
A change relaxed input validation so chapter `0` would be accepted (`Field(ge=1)` -> `Field(ge=0)`).
The CI test suite detected the regression within ~30 seconds of the test job starting, and the
`protect-main` ruleset blocked the merge. The change never reached `main`.

## Impact
None. The change existed only on a short-lived branch and an unmerged pull request.

## Timeline
- Ruleset `protect-main` enabled: PRs required, 5 required status checks, force pushes blocked.
- Direct push to `main` attempted to verify protection: rejected. [CONFIRM]
- Regression pushed to branch `drill/allow-chapter-zero`; pull request opened.
- `Test (pytest + Postgres)` failed after ~30s:
  `test_invalid_create_returns_422[payload0]` -> `assert 201 == 422`.
- Merge button disabled due to failing required check. [CONFIRM]
- PR closed without merging; branch deleted. [CONFIRM]

## Detection
Automated: the API test that asserts chapter 0 is rejected with HTTP 422 returned 201 instead.

## Root cause
The validation rule (`chapter >= 1`) was changed without updating the requirement it encodes.
Chapters are numbered from 1; the test suite encodes that requirement, so the change contradicted it.

## What went well
- The rule was protected by a test written *before* the change (tests encode requirements).
- Required status checks turned the pipeline from a warning light into a gate.
- Recovery was trivial: close the PR. No rollback needed because nothing shipped.

## What went wrong / gaps found
- Before this drill, `main` had no protection: earlier the same day, two runtime version changes
  (Node 24->26, Python 3.14->3.15) reached `main` via quickly merged PRs. The gate closes that gap.
- The failing test name `[payload0]` did not say *what* failed; diagnosis needed a code lookup.

## Action items
| Action | Status |
|---|---|
| Give parametrized test cases readable IDs (`[chapter-zero]` instead of `[payload0]`) | Done (this PR) |
| Keep runtime versions in single sources of truth (`.nvmrc`, `.python-version`) | Done |
| Treat runtime-version PRs (Node, Python) as decisions: read release notes before merging | Ongoing practice |
| Re-run this drill after any change to CI or the ruleset | Ongoing |

## Lessons
A pipeline only protects `main` if merging *requires* it. Tests are executable requirements:
the regression was caught because the rule it broke was written down as a test.
