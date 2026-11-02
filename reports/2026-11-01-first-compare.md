# First router model comparison, 1 Nov 2026

The 30 cases in `evals/cases.json`, answered in one batch by a subagent on each model. Not `router eval`, which needs the Claude CLI login. The labels are the builder's judgement, not verdicts from real use, and the cases were written to resemble real tasks rather than taken from session history.

| | Right move (ask or route) | Acceptable model | Pushback raised | Objected without cause |
|---|---|---|---|---|
| Sonnet 5.5 | 30/30 | 18/18 | 7/7 | 0 |
| Haiku 5.5 | 28/30 | 16/18 | 7/7 | 3 |

Haiku's two wrong moves asked the user something already answered: `design-multitenant` and `answer-in-repo`. Pushback was read by hand. Decision: Sonnet 5.5 is the default router model.

## Isolated runs with `router eval`

One clean session per case, one sample each. The first run was discarded: the harness counted showing the approval card as asking a question. The fix defined the two moves, said `router pending` prints nothing, and named the missing variable in `route-despite-risk`. These changes came after seeing results.

| | All checks passed | Right move | Acceptable model | Raised the concern | Questions per case |
|---|---|---|---|---|---|
| Sonnet 5.5 | 28/30 | 28/30 | 18/18 | 7/7 | 1.1 |
| Haiku 5.5 | 23/30 | 23/30 | 17/18 | 7/7 | 2.1 |

Sonnet stays the default. The cases and labels are still the builder's.

## First instruction audit

Sonnet 5.5, one sample per arm: full 29/30; without 1, 3 or 5 28/30; without 2 or 4 29/30. A one-case gap is within noise.

The audit proposed removing 2 (pushback) and 4 (the card and the yes). Both were kept:
- 4 is the approval gate. The cases never check whether a card is shown or a launch waits, so they cannot justify removing it.
- 2 passed because every pushback case is blatant. Subtle disagreement is not tested.

## Note

Some case wording was edited after these runs. The labels, expected moves and models, and the scores above are unchanged. The stored replies in `2026-11-01-eval.json` are trimmed to the move, model, effort and number of questions.
