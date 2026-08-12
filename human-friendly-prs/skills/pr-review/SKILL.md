---
name: pr-review
description: "Reviews a GitHub PR and leaves human-friendly review comments. Use when asked to review a PR or leave code review comments. Trigger words: `review this PR`, `leave a code review`"
argument-hint: "<PR number, or blank for the current branch>"
---

# PR review

`/code-review` finds the problems. This skill decides which of them are worth a
reviewer's attention, and posts them in the shape a human can skim.

Do not review the diff yourself. Running your own pass alongside `/code-review` gives you
two sets of findings with different standards behind them, and no way to rank one against
the other.

## 1. Resolve the target

```bash
PR="${1:-$(gh pr view --json number -q .number)}"
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
ME=$(gh api user -q .login)
SHA=$(gh pr view "$PR" --json headRefOid -q .headRefOid)
```

If `gh pr view` finds no PR for the current branch, stop and say so.

Stop before reviewing if the PR is closed, is a draft, or already carries a review of
yours posted against this same `$SHA` — a second review of an unchanged head is noise.

## 2. Run the standard review

Invoke `/code-review` for the target, and tell it to hand the findings back rather than
post them:

```
/code-review <PR> — return the findings to me. Do not comment on the PR.
```

It owns what counts as a finding: the diff it reads, the standards it checks, the
confidence bar it filters on. Take its output as given. Do not add findings it did not
raise, and do not resurrect ones it dropped.

If it posts a comment anyway, delete it before you post yours — two reviews of the same
diff under your own login read as a bug:

```bash
gh api -X DELETE "repos/$REPO/issues/comments/<id>"   # only comments authored by $ME
```

If it returns nothing, go to [Nothing found](#nothing-found).

## 3. Assign a priority

Every finding gets `P1`, `P2`, or `P3`. This is the only judgement this skill adds, and
it is what makes the review skimmable — the author reads the P1s and schedules the rest.

- **P1** — merging this ships a defect. Wrong output, data loss, a security hole, or a
  breach of a standard the repo documents in writing.
- **P2** — a real defect with a narrow blast radius. An unhandled edge case, a silent
  failure path, a convention the repo follows everywhere but never wrote down.
- **P3** — a judgement call. Naming, structure, a smell. The author can decline it
  without owing you an argument.

Two rules keep the scale honest:

- Priority is severity, not confidence. A finding you are unsure about does not become a
  P3 — it either survives the review's own confidence bar or it does not get posted.
- Nothing is promoted to make a review look substantial. A PR whose worst finding is a P3
  gets a review whose worst finding is a P3.

## 4. Drop what is already answered

Every comment this skill posts ends with a hidden marker naming the finding:

```html
<!-- review-finding: app/lib/run.ts:42:unsafe-eval -->
```

The slug is a few kebab-case words for the finding itself, so the marker survives the
line moving. Collect the existing markers from comments authored by `$ME`, and drop any
finding already carrying one — a re-review after a push should raise what is new, not
repeat itself.

## 5. Write one comment per finding

```markdown
[AI-generated from automated code review]

### Summary (for humans)

#### P1: Unsafe use of `eval`

**Problem**

- `runExpr` passes the user-supplied `filter` string straight to `eval`

**Suggested fix**

- Parse the filter with `parseFilter` and evaluate the resulting tree

### Extra context (for clankers)

<details>
<summary>Details</summary>

Why it matters, the path that reaches it, what you ruled out, the standard it breaches
and where that standard is written down, alternatives the author might prefer.

</details>

<!-- review-finding: app/lib/run.ts:42:unsafe-eval -->
```

The banner comes first, then both headings at level 3 in that order, nothing between them
and the title.

- The title is `#### P<n>: <short noun phrase>`. Not a sentence, no trailing period.
  Backtick the identifier it is about.
- `**Problem**` and `**Suggested fix**` hold ONLY flat `- ` bullets. Max 3 each, max 100
  characters each.
- Problem bullets are declarative — state what is wrong, at the line you are commenting
  on. "Cache key omits the region."
- Suggested fix bullets are imperative — start with a verb. "Add region to the cache key."
- One finding per comment. Two problems at one line are two comments, or one comment
  whose Problem bullets are genuinely the same defect seen twice.
- Everything long goes in the dropdown. A reader who opens nothing still knows what is
  wrong and what to do about it.

## 6. Post it as one review

One review carrying N inline comments, not N separate comments — the author gets one
notification, and each finding still opens its own thread for `respond-to-comments` to
answer.

Write the roll-up body and each finding to its own file, then assemble:

```bash
jq -n --arg c "$SHA" --rawfile b /tmp/review-body.md \
  '{commit_id:$c, body:$b, event:"COMMENT", comments:[]}' > /tmp/review.json

# once per finding
jq --arg p "app/lib/run.ts" --argjson l 42 --rawfile b /tmp/finding-1.md \
  '.comments += [{path:$p, line:$l, side:"RIGHT", body:$b}]' \
  /tmp/review.json > /tmp/r.tmp && mv /tmp/r.tmp /tmp/review.json

gh api -X POST "repos/$REPO/pulls/$PR/reviews" --input /tmp/review.json
```

Always `event: COMMENT`. This skill does not approve and does not request changes —
that is the human's call, and an automated `REQUEST_CHANGES` blocks a merge queue.

Every `line` must appear in the diff on the `RIGHT` side, or the API rejects the whole
review and you lose all of it. A finding that has no line in the diff — one about
something missing, or about a file the PR did not touch — goes in the roll-up body
instead, under the same `#### P<n>: <title>` structure.

The roll-up body carries the counts and the titles, and nothing else:

```markdown
[AI-generated from automated code review]

### Summary (for humans)

- **3 findings**: 1 × P1, 2 × P2
- **P1**: Unsafe use of `eval` — `app/lib/run.ts:42`
- **P2**: Cache key omits the region — `app/lib/cache.ts:18`
- **P2**: TTL never refreshed on write — `app/lib/cache.ts:64`

### Extra context (for clankers)

<details>
<summary>Details</summary>

The diff reviewed and the head sha, what the review checked, findings it raised that you
dropped and why.

</details>
```

## Nothing found

Post a plain top-level comment. Do not open an empty review, and do not invent a P3 to
justify the run:

```bash
gh pr comment "$PR" --body-file /tmp/clean.md
```

```markdown
[AI-generated from automated code review]

### Summary (for humans)

- **No findings** against `<short sha>`

### Extra context (for clankers)

<details>
<summary>Details</summary>

What was reviewed and what was checked, so the next pass knows what this one covered.

</details>
```

## When NOT to apply this

Skip the structure, and say which of these applied:

- **The repo mandates a review format.** A `CODEOWNERS` checklist or a review template in
  `.github/` wins. Apply the spirit where it costs nothing: lead with the priority and
  the short bullets, fold the long dump into a `<details>` block.
- **The user asked for a conversation, not a review.** "What do you think of this PR?"
  wants an answer in the terminal. Do not post anything to GitHub unless asked to.
- **You wrote the code.** Say so in the roll-up. A review of your own work is worth
  posting, but the author should know which it is.

## 7. Report

Tell the user the PR, the finding count by priority, the files touched by the review, and
anything `/code-review` raised that you dropped in step 4 as already answered.
