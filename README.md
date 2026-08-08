# pr-skills

Two Claude Code skills that give pull requests a consistent shape: short bullets a human
can skim, with the long context folded into a dropdown for the next agent.

## Install

```sh
npx skills add malone-c/pr-skills
```

Add `-g` for a user-level install rather than the current project, and `--skill
pr-description` to take just one. Restart Claude Code afterwards.

## `/pr-description`

Writes and edits PR bodies in this shape:

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

Reasoning, alternatives rejected, file-by-file notes, test evidence, migration steps.

</details>
```

Problem bullets are declarative, Fix bullets are imperative. Max 7 per section, max 100
characters each — they are read at a glance, not studied. Everything long goes in the
dropdown.

The skill deliberately stands down when the description was written by a co-contributor,
when the PR already has content in another shape, or when you have asked for something
that does not fit the structure cleanly.

## `/respond-to-comments`

```
/respond-to-comments [PR number]
```

Defaults to the PR for the current branch. Collects inline review comments, top-level
comments, and review summaries; skips resolved and outdated threads; then for each
unanswered comment investigates the claim against current `HEAD`, decides whether to
accept it, commits accepted fixes, and replies in a fixed shape:

```
Identified problem: <=20 words
Suggested fix: <=20 words
Decision: Accepted
- reason
- reason

### Extra context

What was checked, what was ruled out, the fix commit sha.
```

Each reply ends with a hidden `<!-- responded-to: <id> -->` marker, which is how the skill
knows what it has already answered — GitHub does not thread top-level comments, so
without it the "new comments only" check would be guesswork.

## `/pr-loop`

```
/pr-loop [PR number] [interval]
```

Answers review comments on a timer until the reviewers go quiet. Defaults to the PR for
the current branch and a 10 minute interval; creates the PR with `/pr-description` first
if the branch has none.

Each pass runs `/respond-to-comments` and updates a counter. Answering something resets
it; finding nothing adds one. At two consecutive quiet passes the loop disarms itself.
It also stops as soon as the PR leaves the `OPEN` state.

The timer is a session-scoped cron job, so it lives only as long as the Claude Code
session, fires only while that session is idle, and expires after 7 days.

## Troubleshooting

If a skill does not appear after install, restart Claude Code. Skills are read at
startup, so a running session will not see a newly installed skill.

If `npx skills update` reports no changes, clear the cache with `rm -rf ~/.npm/_npx`.

## License

MIT
