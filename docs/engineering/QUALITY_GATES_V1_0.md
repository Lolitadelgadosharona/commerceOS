# Commerce OS Quality Gates v1.0

Status: mandatory pull-request baseline; exact commands are frozen during Sprint 001 scaffolding

## Merge policy

Every change enters through reviewable commits and a pull request. Required checks must run in GitHub Actions from a clean checkout using locked dependencies. The author cannot waive a failed gate. Higher-risk changes require review from the owning domain plus Security/Privacy, Finance, or Governance when those boundaries are affected.

## Required gates

| Gate | Required evidence | Failure condition |
|---|---|---|
| Formatting | Deterministic Python and TypeScript/Markdown formatting check in non-write mode | Any formatter diff or trailing-whitespace/encoding failure |
| Lint/static analysis | Python lint and type checks; TypeScript/Next.js lint and type checks; dependency/import-boundary rules | Error, unsafe suppression without rationale, or prohibited domain dependency |
| Unit tests | Pytest domain/application tests and frontend unit/component tests selected during scaffolding | Any failure or unreviewed test deletion |
| Integration/contract tests | PostgreSQL/Redis integration, OpenAPI/event compatibility, authorization and idempotency tests | Failure, schema drift, direct cross-domain storage access, or unauthorized behavior |
| Browser tests | Playwright critical owner workflow smoke tests when UI behavior changes | Relevant critical path fails or trace shows uncaught error |
| Migrations | Single Alembic head; upgrade from baseline/current production snapshot; downgrade/rollback strategy; model/schema drift check; reviewed SQL | Destructive/unbounded lock risk, missing backfill/rollback, auto-create reliance, or migration fails |
| Documentation | Markdown structure/lint, relative links, architecture index, API/event schema docs, decision/runbook updates | Broken link, stale contract, undocumented breaking/authority/data change |
| Security/privacy | Secret scan, dependency vulnerability review, authorization/adversarial tests, data-flow/retention review when applicable | Secret exposure, critical unresolved issue, privilege bypass, unreviewed PII/provider transfer |
| Build/container | Reproducible Next.js/FastAPI/worker build; Docker image build and basic health check | Build failure, mutable/unpinned critical base policy, root/unnecessary-secret issue |

## Pull-request requirements

The PR describes purpose, scope, owning domain, contracts/data affected, migrations, security/privacy/financial authority impact, compatibility, tests, rollout, and rollback. It links an approved issue/plan and identifies non-goals. Generated files must be reproducible and reviewed through their source schemas.

## Migration-specific policy

- Application schema creation occurs only through Alembic; tests begin from migrations, not ORM `create_all` as production proof.
- Prefer expand/migrate/contract. Destructive contraction is separated until compatibility telemetry and rollback windows close.
- Data backfills are bounded, observable, idempotent, restartable, and do not conceal ambiguous identity matches.
- Every migration records owner, expected duration/locking, backup/recovery assumption, and forward/rollback action.

## Coverage and exceptions

Coverage thresholds are set from the Sprint 001 baseline and may only increase or be replaced by stronger risk-based gates. Coverage percentage never substitutes for boundary, authority, migration, or adversarial tests. A temporary exception requires an owner, reason, risk assessment, compensating control, expiry, and tracked remediation; constitutional human-approval, security, privacy, and audit invariants are not waivable through ordinary PR exception.

## Branch protection target

Once a remote exists, protect the default branch: require pull requests, required status checks, current-branch review, resolved conversations, and no force push/deletion. Limit workflow token permissions and protect production environments with human approval.
