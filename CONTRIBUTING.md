# Contributing

Thanks for your interest in improving AstroHealth.

## Workflow

1. Branch from `main` with a short, descriptive name (`be/...`, `fe/...`, `ai/...`, `contract/...`).
2. Shape-of-data changes happen only in `contracts/openapi.yaml` — then run `make gen`
   and update `contracts/CHANGELOG.md`.
3. `make check` must pass before every push. CI runs the exact same command.
4. Keep pull requests small and single-purpose; squash-merge.

## Ground rules

- Generated files (`packages/contracts_py`, `apps/web/src/api/schema.d.ts`) are never
  edited by hand — change the spec, then regenerate.
- No secrets, no raw datasets, no build artifacts in commits.
- Every forecast ships with its warnings and disclaimer — keep that contract intact.
