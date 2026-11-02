# How it got here

task-router is a 349-word skill and one Python file, small on purpose. This note covers why, how its instructions were tested, and what the tests can't tell you.

## The starting point

In July 2026 Anthropic wrote that it had removed over 80% of Claude Code's system prompt for its Claude 5 generation models "with no measurable loss on our coding evaluations", and that it had been overconstraining Claude Code through its system prompt, CLAUDE.md files and skills ([The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models), Thariq Shihipar, 24 July 2026). The post closes by suggesting you may need to simplify your own setup in the same way.

At Y Combinator's Startup School the same month, Boris Cherny, who created Claude Code, described how the team does it: on each new model they delete the system prompt and bring it back line by line to see what each line does, which researchers call ablation. His advice to people using Claude Code was to delete their CLAUDE.md and skills every six months, use the model, and add an instruction back "only when you see it repeatedly stumble on the same thing" ([Boris Cherny: We Cut 80% of Claude Code's Prompt](https://www.ycombinator.com/library/UN-boris-cherny-we-cut-80-of-claude-code-s-prompt), YC Startup Library).

Both are Anthropic's reports about its own product, and the post doesn't publish the evaluations behind "no measurable loss".

## The method

Turned into steps you can run on any setup:

1. **Inventory.** Measure everything an agent reads, including what loads before any task.
2. **Classify each instruction** as one of four things:
   - a *guardrail*, which protects money, people, your authority or the repository;
   - a *fact*, a dated truth about a tool, a price or the project's state;
   - a *correction*, which is coaching, or a lesson from a past mistake;
   - *history*, a record of a past session, which isn't an instruction at all.
3. **Ablate.** Take tasks a person has already judged, and run each twice from the same inputs, in fresh headless sessions with no ambient configuration:
   - the *full* arm gets every instruction;
   - the *lean* arm gets only the guardrails, the facts and the task's own contract.

   Score both against the recorded verdicts, blind to which arm wrote what.
4. **Default to lean.** An instruction that doesn't make the recorded tasks better comes out of what is always loaded. Archive it rather than erasing it.
5. **Add back only after a repeat.** An instruction returns only when its fault happens again, after removal, in two independent sessions. When a fault repeats, a check in code or a fix to the input usually beats more prose.
6. **Propose, never delete.** Every removal is a proposal a person approves, saying where the instruction came from.
7. **Re-run on every model change, and every six months.** Schedule it rather than relying on memory.

## Building the router that way

The router was built lean from the start.

- **The skill holds only what a model couldn't work out alone.** That came to five numbered instructions: understand the goal, push back when there is a reason, choose from the catalog, show a card and wait for a yes, and write a brief for a worker that starts knowing nothing.
- **What must never depend on judgement is code, not prose.** That covers the Codex sandbox flags, which models may launch, per-project provider blocks, and refusing briefs that contain secrets or are too large.
- **A test caps the skill at 350 words**, so it can't creep.

Then the same method was run on the router itself (`router audit`). It used 30 cases on Sonnet 5.5, one sample per arm. The full skill passed 29 of 30. Removing any single instruction gave 28 or 29. A one-case gap is noise, so on these cases no instruction clearly earned its place.

The audit proposed removing two of them. Both were kept:

- **The card and the wait for a yes stayed.** No case checks whether a card is shown or a launch waits, so the eval can't see that instruction work. It is the approval gate, and a guardrail doesn't go to a vote it can't be measured in.
- **The pushback instruction stayed.** Every pushback case in the set is blatant, so subtle disagreement was never tested.

That is the most useful lesson here: an ablation can only remove what your cases measure. Before deleting an instruction because removing it didn't hurt, check whether your cases could ever have shown the harm.

Separately, Sonnet 5.5 beat Haiku 5.5 as the router model, 28 of 30 against 23 of 30. All seven of Haiku's misses were questions where the case expected a route.

## Limits

- **Tiny samples.** 30 router cases, one sample per arm. Read the direction, not the decimals.
- **The labels are the builder's.** The router's cases were written and labelled by the Claude session that built it, not taken from real use.
- **One model family.** Claude models answered the cases and a Claude model judged the pushback. A judge from another family is the obvious next check.
- **The harness was fixed after seeing results.** The first router eval counted the approval card as a question and was thrown out.
- **Some case wording was edited after the runs.** Labels and scores are unchanged.
- **None of this is a benchmark.**

## If you copy it

- Keep guardrails in code and out of the vote.
- Write cases from tasks you actually ran, with verdicts from the person who owns the work.
- Run the audit when the model changes, and accept "remove" only for things your cases can see.
- Log every real route with an outcome, because that log is the evidence that will eventually matter more than the evals.
