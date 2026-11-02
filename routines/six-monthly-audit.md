Six-monthly instruction audit for task-router, in its local checkout (for example ~/task-router).

Rules: propose only. Never edit skills/route/SKILL.md or evals/removed.json. The only spend allowed is this audit's model tokens, capped by --max-usd. The report holds costs and replies, so it stays in ~/.local/state/task-router/reports/ and is never committed.

1. In the checkout, run `git pull --ff-only`.
2. Run `router audit --max-usd 15` and `router addback`.
3. Final message, at most 10 lines: each arm's result next to the full version, the proposed removals, the add-back list, the report's path and anything that failed, ending with "Nothing changes until the owner approves each removal."
