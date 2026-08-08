# pr-skills

Two Claude Code skills that give pull requests a consistent shape: short bullets a human
can skim, with the long context folded into a dropdown for the next agent.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/malone-c/pr-skills/main/install.sh | sh
```

Writes to `$CLAUDE_CONFIG_DIR/skills` (default `~/.claude/skills`). Restart Claude Code
afterwards. To read the script before running it, open
[`install.sh`](install.sh) — it copies two Markdown files and changes nothing else.

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

## License

MIT
