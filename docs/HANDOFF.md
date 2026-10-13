# Small-session build workflow

Use a fresh implementation session pointed at this repository. Assign one task, not
“build everything.” The first four tasks are sequential because each uses the prior
contract. Keep prompts and STATUS.md short; do not paste platform files or chat history.

Copy this prompt:

> Work in this repository. Read AGENTS.md and STATUS.md, then implement T01 from
> docs/TASKS.md. Follow docs/SPEC.md. Complete only T01, run its acceptance checks,
> and update STATUS.md with results, blockers, and the next task. Do not implement
> later tasks or publish anything. If a settled choice works, use it without research.

For the next session replace T01 with T02, etc. A smaller coding model can be assigned
a bounded task; evaluate it by the checks rather than assuming a model guarantees
correctness. Request a focused review of the API boundary and process lifecycle after
T03. No automatic multi-agent orchestration is required.

If blocked: record the exact failure and smallest missing input. Do not spend a whole
session repeatedly retrying authentication or exploring unrelated architecture.

A useful final report is four lines: implemented; checks; limitations; next task.
