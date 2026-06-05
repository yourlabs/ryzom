---
name: code-walkthrough
description: Produce an annotated code walkthrough of a change/feature/topic — gather all the code written for it AND the existing code it uses/depends on, then present full snippets with file:line context and a short explanation of each. Use when asked to "walk through", "explain the code for", "show all the code for", "give a tour of", or "annotated review of" something (a tier, feature, commit, PR, or topic). This is explanatory, not a bug hunt — for correctness/bug review use /code-review instead.
---

# Code walkthrough

Goal: make a change **legible**. Given a target ("something" — a feature, a tier of
work, a commit/range, a PR, or a topic), collect every relevant piece of code — both
what was **made** for it and what it **uses** — and present each as a full snippet
with just enough context and a plain-language explanation. Read-only: never edit.

## 1. Resolve the target → the set of code that was *made*

Pin down exactly what changed. Use whatever the user gave you:

- A topic/feature name → find the files/symbols by searching (Grep/Glob), and check
  recent commits whose messages mention it: `git log --oneline -15`.
- A commit / range / branch → `git show <ref>` or `git diff <base>..<head>`.
- A PR number → `gh pr diff <n>` (and `gh pr view <n>`).
- "the last change" / uncommitted work → `git diff` and `git diff --staged`.

Produce the **made** set: the exact functions/blocks added or modified (quote the
*current* file content with `file:line`, not the raw diff — diffs read poorly).

## 2. Follow the references → the code it *uses*

For each made snippet, trace what it depends on so the reader doesn't have to:

- Every non-trivial symbol it calls/constructs (helpers, widgets, classes, APIs) —
  jump to that definition and include it. One hop is usually enough; go a second hop
  only when the first doesn't explain the behavior.
- Cross-file contracts it relies on (an event name, a CSS class/`data-*` the JS keys
  off, a settings flag, a signal). Include the other side of the contract.
- Skip the obvious (stdlib, language builtins, trivial one-liners). Quality over
  completeness — include what a reviewer would otherwise have to go look up.

## 3. Present the walkthrough

Order it so it reads top-down: **entry point → what was made → what it uses →
synthesis**. For *each* snippet:

````
### <short title> — `path/to/file.py:LINE`
<one line: what this is and why it's here>

```python
<the FULL snippet — the whole function/block, not an excerpt>
```

<2–4 sentences: what it does, how it connects to the rest, any subtlety worth
flagging (a constraint it honors, a gotcha, a default). Link with file:line.>
````

Rules for the output:
- **Full snippets**, not fragments — show the entire function/block being discussed.
- Keep prose tight: a sentence or two of context before, an explanation after.
- Group: "Made for this change" first, then "Code it relies on", then a short
  **Synthesis** (how the pieces fit + anything notable, e.g. a deliberate trade-off).
- Mention what you deliberately left out and why (so scope is clear).
- It's a tour, not a verdict — note a genuine risk in passing, but don't turn it
  into a bug review (that's `/code-review`).

## Notes

- This is read-only and presentational; it makes no changes and runs no mutating
  tools.
- Snippets must be quoted from the **current** working tree (or the named ref), so
  line numbers are clickable and accurate.
- For a large target, walk the core path in full and summarize the long tail rather
  than dumping every file.
