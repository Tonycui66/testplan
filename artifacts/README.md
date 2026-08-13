# QA Artifacts

This directory is the shared structured-artifact area defined by
`multica-team-spec.md`, section 5. Agents write their machine-readable outputs
here instead of relying on free-form comments.

## Layout

```text
artifacts/
├── tasks/       # task payloads created by LEAD-QA
├── reviews/     # review results created by AGT-CODE-REVIEW
├── qa/          # test-design matrices and checklists
├── author/      # diffs and author verification artifacts
└── status/      # current phase status and handoff state
```

Every substantive artifact must contain at least:

- `agent_id`
- `task_id`
- `created_at`
- `input_artifacts`
- `output_artifacts`
- `status`
- `handoffs`
- `gaps`
- `risks`

Placeholder `README.md` files keep empty directories representable in Git.
They are not agent deliverables.

## Current Manifest

This branch changes:

```text
README.md
artifacts/README.md
artifacts/tasks/README.md
artifacts/reviews/README.md
artifacts/qa/README.md
artifacts/author/README.md
artifacts/status/phase-status.json
```
