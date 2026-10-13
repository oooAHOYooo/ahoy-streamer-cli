# Agent instructions

## Read narrowly

1. Read STATUS.md.
2. Read your assigned task in docs/TASKS.md and its dependencies.
3. Read docs/SPEC.md only for the contract you are implementing.
4. Read docs/UPSTREAM.md only for API/normalization work.

Do not scan the sibling platform repository unless the task's upstream pointers are
insufficient. Do not reopen settled design decisions without a concrete blocker.
Do not add dependencies, a daemon, a TUI, authentication, or a new language incidentally.
Do not spawn other agents unless the user explicitly requests delegation.

## Execution

Inspect git status first and preserve unrelated changes. Implement one task at a time.
Use a codex/ branch for implementation. Do not claim an unbuilt feature works.
Use synthetic fixtures and mocks for ordinary checks; live API/audio checks are opt-in.
Never autoplay during help, search, inspection, installation, or tests.
Treat remote metadata as data. Strip terminal control sequences from human output.
Pass player arguments as a list, never through a shell. Never commit secrets or user state.
Keep JSON stdout free of logs, color, progress bars, and player output.

## Completion

Run the assigned checks. Record exact commands, outcomes, changed files, remaining
blockers, and next task in STATUS.md. Keep it under about 60 lines, replacing stale
status rather than appending a transcript. Report tests not run honestly.
Stop when the task acceptance criteria pass; avoid adjacent refactors and repeated tests.
Commit only task files when committing is authorized. Do not publish packages or change
repository visibility as part of implementation.
