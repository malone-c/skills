# human-friendly-prs

Claude Code skills that give pull requests a consistent shape: short bullets a human can
skim, with the long context folded into a dropdown for the next agent.

Not published yet. The install instructions and the self-advertising template lines have
been stripped — see [Before publishing](#before-publishing) for what to put back.

## `/pr-description`

Writes and edits PR bodies in this shape:

```markdown
[AI-generated]

### Summary (for humans)

#### Problem

- Cache key omits the region, so us-east reads hit eu-west entries
- Stale entries survive deploys because the TTL is never refreshed

#### Fix

- Add region to the cache key
- Reset the TTL on every write

### Extra context (for clankers)

<details>
<summary>Details</summary>

Reasoning, alternatives rejected, file-by-file notes, test evidence, migration steps.

</details>
```

Problem bullets are declarative, Fix bullets are imperative. Max 7 per section, max 100
characters each — they are read at a glance, not studied. Everything long goes in the
dropdown.

A PR carrying several distinct changes gets one `#### Issue N: <title>` heading each inside
the summary, with Problem and Fix as bold labels underneath.

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

```markdown
[AI-generated from automated review flow]

### Summary (for humans)

- **Identified problem**: <=20 words
- **Suggested fix**: <=20 words
- **Decision**: Accepted
- **Reason**: <=20 words

### Extra context (for clankers)

<details>
<summary>Details</summary>

What was checked, what was ruled out, the fix commit sha.

</details>
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

## Before publishing

Three things were removed while these skills are private. Put them back when they are
ready to ship, and fix the repo slug first — this used to live at `malone-c/pr-skills`
and now lives under `malone-c/skills`, so `npx skills add` needs whatever path the new
layout actually resolves to.

**1. An install section, here in this README:**

````markdown
## Install

```sh
npx skills add malone-c/skills
```

Add `-g` for a user-level install rather than the current project, and `--skill
pr-description` to take just one. Restart Claude Code afterwards.
````

**2. The last line of the PR body template**, in `skills/pr-description/SKILL.md`, after
the closing `</details>` and inside the fenced example:

```markdown
To install [this GitHub PR template](https://github.com/malone-c/skills): run `npx skills add malone-c/skills`
```

Followed, outside the fence, by: *The install line is part of the template — keep it as
the last line of every body.*

**3. The last visible line of the reply template**, in
`skills/respond-to-comments/SKILL.md`, between the Extra context paragraph and the
`<!-- responded-to: COMMENT_ID -->` marker:

```markdown
To install [this GitHub comment template](https://github.com/malone-c/skills): run `npx skills add malone-c/skills`
```

Followed, outside the fence, by: *The install line is part of the template — keep it as
the last visible line of every reply.*

Lines 2 and 3 are the ones that show up on every PR and every review reply. They are
advertising, so they only belong there once the skills are public and the link resolves.

## License

MIT
