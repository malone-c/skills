---
name: pr-description
description: "Makes PR descriptions human-friendly. Use always when writing or editing PR descriptions. Trigger words: `open a PR`, `create a PR`, `update the PR description`"
argument-hint: "<PR number, or blank for the current branch>"
---

# PR description

Two audiences share one body. The bullets are for a human deciding whether to review
this; the dropdown is for the agent that has to understand it. Keep them apart.

## Format

```markdown
# Problem

- Cache key omits the region, so us-east reads hit eu-west entries
- Stale entries survive deploys because the TTL is never refreshed

# Fix

- Add region to the cache key
- Reset the TTL on every write

# Extra context

<details>
<summary>Details</summary>

Everything you would normally put in a PR description: reasoning, alternatives
rejected, file-by-file notes, test evidence, migration steps, risk.

</details>
```

## Several changes in one PR

When the PR carries more than one distinct change, give each its own `# Issue N: <title>`
heading and demote Problem and Fix to level 2 underneath it. One `# Extra context` at the
end still covers the whole PR.

```markdown
# Issue 1: Cache key ignores the region

## Problem

- us-east reads hit eu-west entries

## Fix

- Add region to the cache key

# Issue 2: Stale entries survive deploys

## Problem

- The TTL is never refreshed

## Fix

- Reset the TTL on every write

# Extra context

<details>
<summary>Details</summary>

...

</details>
```

Titles are short noun phrases, not sentences. Only split when the changes stand on their
own — steps toward one goal are a single Problem/Fix, and splitting them makes the PR look
bigger than it is.

## Rules

- Level-1 headings in order, nothing before the first one. Either `# Problem`, `# Fix`,
  `# Extra context`, or a run of `# Issue N: ...` followed by `# Extra context`.
- Problem and Fix hold ONLY flat `- ` bullets. No prose, no sub-bullets, no sub-headings.
- Max 7 bullets per section, max 100 characters each. They are read at a glance.
- Problem bullets are declarative — state what is wrong. "Cache key omits the region."
- Fix bullets are imperative — start with a verb. "Add region to the cache key."
- Every bullet stands alone. A reader who opens nothing still knows what changed and why.
- One idea per bullet. If a bullet needs a comma-spliced clause to make sense, it belongs
  in the dropdown.
- Everything long goes inside `<details>`. Resist putting it in the bullets — a wall of
  text under `# Problem` defeats the entire format.

## When NOT to apply this

Skip the structure, and say which of these applied:

- **Someone else wrote it.** Compare the PR author against `gh api user -q .login`. Never
  restructure a co-contributor's description — you would be rewriting their words.
- **Pre-existing content that does not fit.** If the body already has content in another
  shape, do not force it into these headings. Add to it in its own style, or ask.
- **The user asked for content that does not fit cleanly.** A table, an image, a checklist,
  a release note, a template the repo mandates. Their request wins.

In the second and third cases, still apply the spirit where it costs nothing: lead with
short bullets, fold the long dump into a `<details>` block.

## Applying it

Write the body to a file and pass `--body-file` — heredocs mangle backticks and `$`.

```bash
gh pr create --title "..." --body-file /tmp/pr-body.md
gh pr edit <number> --body-file /tmp/pr-body.md
```

Editing an existing PR replaces the whole body. Read it first with
`gh pr view <number> --json body -q .body` and check it against the exceptions above
before you overwrite anything.
