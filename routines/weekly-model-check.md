Weekly model check for task-router, in its local checkout (for example ~/task-router).

1. In the checkout, run `git pull --ff-only`, then `router check-models --write`.
2. Exit 0: nothing changed. Finish with one line saying so.
3. Exit 1: a source failed and nothing was changed for it. Report which source, in one line.
4. Exit 10: the catalog changed. Run `python3 -m unittest discover tests`. If the tests pass, commit only catalog.json with the message "Catalog: <what changed>" and push to main. Status changes are facts from the providers, so they need no review.
5. Report what was added and retired. If a retired model was the only active one of its kind, say so, and recommend which trial model the owner should promote with `router set-status`. Promoting is the owner's decision; never do it here.
6. If the model named as the default in `router start` was retired, or a new one was added at its level, also run `router eval --models <old> <new> --max-usd 5` and report the result, because instructions written for an older model may no longer be needed.
