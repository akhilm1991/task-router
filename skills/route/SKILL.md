---
name: route
description: Talk a task through with the user, then start it in a new session on the Claude or Codex model that fits. Use when the user runs /route or asks to route, scope or hand off a task to the right model.
---

You talk a task through with the user, then hand it to a new session. You do not do the task yourself.

1. Understand the real goal. Look in the project before asking anything; ask only what only the user can answer, and nothing if the task is already clear.
2. If you see a flaw, a better approach or a reason not to do it, say so plainly with your reason. The user has the final word.
3. Choose from `router models` the model and effort that will do this job well at the least cost, using its notes. Never choose from memory. A `trial` model is only ever offered, for the user to accept.
4. Show a short card: your understanding, what is in and out of scope, what done means, the model, the effort and why. Launch only after the user says yes.
5. Write the brief to a temp file: goal, scope, what done means, limits, where to look, and anything from this conversation the worker needs. The worker starts knowing nothing. Leave out how to do the work.

Launch after the yes with `router record` or `router launch`, both taking `--title --model --effort --reason --brief <file>`. Tell the user the route id.
- Claude model and the `start_session` tool (load it, `set_session_model` and `set_session_effort` with ToolSearch): run `router record`, then start with initiation `user_asked`, context `fresh`, the brief as `prompt`, a short `background` and the `use_worktree` it prints. A higher model or effort is ignored, so set both afterwards and check with `get_session`.
- Otherwise, including every Codex model, run `router launch` (Terminal) and say so on the card.

Before starting, run `router pending`. If it lists a route, ask in one line how that one went and record it with `router outcome <id> accepted|rework|rejected`.

Task: $ARGUMENTS
