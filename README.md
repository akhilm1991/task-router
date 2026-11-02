# task-router

You describe a task. A cheap model talks it through with you, pushes back if it sees a problem, then starts the work in a new session on the Claude or Codex model that fits it, at the effort it needs.

It is a short skill (`/route`, under 350 words) and one Python file (`bin/router`) that holds the parts that must not depend on a model's judgement: the model list, a few hard limits, launching and logging. It is not an agent framework, a scheduler or a cost dashboard.

Results so far are early. See [Status and limits](#status-and-limits).

## Install (about a minute)

Needs Python 3.9+ (standard library only), plus the `claude` and `codex` CLIs, each already logged in. Opening a new Terminal window from the desktop app works on macOS only.

```bash
git clone https://github.com/akhilm1991/task-router ~/task-router
```

```bash
~/task-router/install.sh
```

`install.sh` links `router` into `~/.local/bin` and the skill into `~/.claude/skills/route` and `~/.codex/skills/route`. Then check that both CLIs can make a call:

```bash
router doctor
```

If your shell sets an API key or base URL for Claude that you don't want the router to use, put `{"direct_login": true}` in `~/.config/task-router/config.json`. The router then ignores those `ANTHROPIC_*` settings and uses your normal `claude` login.

## Use

Type `/route what you want done` in a Claude or Codex session, or start from a terminal:

```bash
router start "what you want done"
```

`router start` opens a Sonnet session for the conversation. `/route` runs on the current session's own model, because a skill can't switch the model for more than one turn.

The router looks in the project before asking anything, asks only what it can't find out, says so if it disagrees, and shows a card (goal, scope, what done means, model, effort and why). Nothing starts until you say yes. It then writes a brief for the worker, which starts knowing nothing else.

## Where the task starts

| You run `/route` in | What happens |
|---|---|
| The Claude desktop app (Code tab) | `router record` checks and logs the route. The app's `start_session` tool opens a new app session with the brief, and the skill then sets that session's model and effort. |
| A terminal | `router launch` runs `claude` or `codex` right there. |
| Codex, or for any Codex model | Codex models can't run as Claude app sessions, so `router launch` runs the Codex CLI in the terminal, or opens a Terminal window if there is none. |

`record` and `launch` refuse the same things (see the table below). `record` starts nothing itself and logs `"via": "app"`.

Checked in the desktop app in November 2026: `start_session` quietly caps the new session at the calling session's model and effort, so a Sonnet session asking for Opus gets Sonnet. Calling `set_session_model` and `set_session_effort` on the new session afterwards does move it up, and the app may ask you to approve that. A session's own answer about its effort is unreliable, so the skill checks with `get_session`. If the app tools are missing or refuse, the skill falls back to `router launch`.

Git projects get their own worktree, so two sessions never write to the same checkout. A folder that isn't a git repo is shared, and the router says so.

## What stays in code

The model makes the judgement calls. Code holds only what must never depend on judgement:

| Limit | Where in `bin/router` |
|---|---|
| Codex always runs with `workspace-write` and `on-request`, whatever your Codex config says | `build_command` |
| Only `active` or `trial` models can launch | `plan_route` |
| A project can refuse a provider: `.router.json` with `{"blocked_providers": ["openai"]}` | `project_blocks` |
| Briefs containing an obvious secret, or over 16 KB, are refused | `plan_route` |

Codex's sandbox still allows writes to temp folders. The secret check is a short regex for common key formats, not a scanner.

An instruction belongs in `skills/route/SKILL.md` only if the model can't work it out alone. A test keeps that file under 350 words.

## Models

`catalog.json` lists the models and a one-line note on each. The router reads it on every run and never chooses from memory.

- `router check-models --write` compares it with `codex debug models` and Anthropic's models page. New models arrive as `trial`; models no longer named become `retired`. Exit code 10 means something changed.
- `router stats` shows your results per model. `router set-status <model> active` promotes one. That is your call, not the router's.
- Private notes go in `~/.config/task-router/catalog.local.json`, as `{"models": [{"id": "...", "note": "..."}]}`.

## Testing the instructions

The idea behind the project is in [docs/how-it-got-here.md](docs/how-it-got-here.md): newer models need less handholding, so test each instruction by removing it, and add one back only when its fault repeats.

- `router eval --models <a> <b>` runs the 30 cases in `evals/cases.json` on each model, one clean headless session per case, and checks the move (ask or route), the model and, where a case expects it, the pushback. A second model judges the pushback.
- `router audit` removes each numbered instruction in turn and re-runs the cases. It proposes removals and never edits anything. The cases test the move, the model and the pushback. They don't test whether a card is shown or a launch waits for a yes, so a proposal to remove that instruction is not evidence.
- `router addback` checks the instructions listed in `evals/removed.json`. One comes back only when its fault repeats in two independent sessions, recorded with `router outcome <id> rework --fault <removed-id>`.

`eval` and `audit` spend model tokens and take a `--max-usd` cap. They write their reports to `~/.local/state/task-router/reports/`, outside the repo. The example runs in `reports/` are the ones described in this README.

## Routines

`routines/` holds a weekly model check and a six-monthly audit, written as prompts for a scheduled agent. Schedule them however you like. Both only propose changes, except that the weekly check may commit catalog status changes, which are facts from the providers.

## Log

Routes are logged in `~/.local/state/task-router/routes.jsonl`. `router pending` lists ones with no outcome, and `/route` asks about one at the start of the next task.

## Adding a provider

1. Add its models to `catalog.json` with a new `provider` value.
2. Add a branch to `build_command` that builds its CLI command, with its sandbox flags set there.
3. If its CLI reads its own rules file (like `CLAUDE.md` or `AGENTS.md`), add it to `PROVIDER_FILES`.
4. Optionally add a fetch function to `cmd_check_models` and a line to `cmd_doctor`.
5. Add a test next to `test_codex_is_always_sandboxed`.

## Status and limits

- **The evidence is thin.** 30 cases, written and labelled by the Claude session that built the router rather than by the person using it, and made to resemble real tasks rather than taken from them. One sample per arm. A one-case difference is noise.
- **One model family judged it.** The cases were run on Claude models, and a Claude model judged the pushback.
- **The harness changed after seeing results.** The first eval run was thrown out because it counted the approval card as a question; the fix is recorded in `reports/2026-11-01-first-compare.md`.
- **Some case wording was edited after the recorded runs.** Labels and scores are unchanged. Re-run `router eval` to get results for the published wording.
- **Model ids date fast.** `catalog.json` reflects November 2026.

## Tests

```bash
python3 -m unittest discover tests
```

## License

MIT, see [LICENSE](LICENSE).
