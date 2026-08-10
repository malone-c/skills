---
name: respond-to-comments
description: Work through review comments on a GitHub PR. Use when asked to respond to PR comments or review feedback
argument-hint: "<PR number, or blank for the current branch>"
---

# Respond to PR comments

Answer every review comment on a PR that has not been answered yet. One comment at a
time: investigate, decide, fix if accepted, reply.

## 1. Resolve the target

```bash
PR="${1:-$(gh pr view --json number -q .number)}"
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
ME=$(gh api user -q .login)
```

If `gh pr view` finds no PR for the current branch, stop and say so.

## 2. Collect comments

Three sources, all of them:

```bash
gh api "repos/$REPO/pulls/$PR/comments" --paginate   # inline, threaded via in_reply_to_id
gh api "repos/$REPO/issues/$PR/comments" --paginate  # top-level conversation
gh api "repos/$REPO/pulls/$PR/reviews" --paginate    # review summary bodies
```

Skip resolved and outdated inline threads — those points are settled:

```bash
gh api graphql -f query='
  query($owner:String!,$name:String!,$pr:Int!){repository(owner:$owner,name:$name){
    pullRequest(number:$pr){reviewThreads(first:100){nodes{
      isResolved isOutdated comments(first:50){nodes{databaseId}}}}}}}' \
  -f owner="${REPO%/*}" -f name="${REPO#*/}" -F pr="$PR"
```

## 3. Filter to unanswered

Every reply this skill posts ends with a hidden marker naming the comment it answers:

```html
<!-- responded-to: 1234567 -->
```

Collect those ids from all comments authored by `$ME`. A comment is unanswered if its
id is not in that set.

Then drop everything that is not actually review feedback:

- **Status automation.** Preview deploy links, coverage reports, CI summaries, and
  bundle-size tables are not asking you for anything. Judge by content, not by author:
  a machine login is not grounds for skipping. Review bots — Codex, Claude, Copilot,
  Vercel Agent — are the main source of feedback this skill exists to answer, and
  dropping them leaves the PR unaddressed.
- **Replies this skill already posted** — any comment whose body contains
  `responded-to:`. This is what stops you answering yourself, so match on the marker, not
  on the author. The PR author is usually the Claude Code user, and their notes on their
  own PR are exactly the work you were asked to do.
- **Pure-approval reviews** with empty bodies.
- **Comments with no ask in them** — "nice", "thanks for fixing", ":shipit:". Answering
  these with a formal decision block reads as sarcasm.

If nothing survives, say so and stop.

## 4. Investigate, then decide

For each unanswered comment, in the order posted:

- Read the code the comment points at. Do not reason from the comment text alone.
- Check whether the claim actually holds at current HEAD — reviewers comment on stale diffs.
- Look for the same pattern elsewhere in the file; a reviewer often names one instance of many.

Accept when the comment identifies a real defect, a real violation of a documented
convention, or a genuinely simpler equivalent. Reject when the claim does not hold at
HEAD, the suggestion breaks something the reviewer could not see, it is a preference
with no basis in the repo's conventions, or it is correct but out of scope for this PR
— in the last case say so in the reasons and note the follow-up in Extra context.

Report the decision you actually reached. Accepting a weak suggestion to avoid friction
makes the codebase worse and the reply useless.

## 5. Apply accepted fixes

Make the change and commit it per accepted comment, one-line commit message, no mention
of Claude. Push once after the whole loop, before posting any replies, so every reply
can cite a sha that exists.

## 6. Reply

Write each reply to a file and post it verbatim:

```markdown
[AI-generated from automated review flow]

### Summary (for humans)

- **Identified problem**: <=20 words, the problem the commenter identified
- **Suggested fix**: <=20 words, the fix the commenter suggested
- **Decision**: Accepted
- **Reason**: <=20 words, why

### Extra context (for clankers)

<details>
<summary>Details</summary>

Justification detail, what you checked, what you ruled out, follow-ups. Cite the fix
commit sha when accepted.

</details>

<!-- responded-to: COMMENT_ID -->
```

The banner line comes first, then both headings at level 3 in that order. Nothing else
before `### Summary (for humans)`.

The four summary bullets are flat, in that order, each `- **Label**: ` followed by one
plain sentence — no sub-bullets, no nesting. `**Decision**` is exactly `Accepted` or
`Rejected` and nothing else. Add a second `- **Reason**: ` bullet if one clause genuinely
will not carry it, no more.

Everything long goes inside the `<details>` block. The summary is read at a glance; a
reader who never opens the dropdown still knows what was raised and what you did about it.

Post to the right place:

```bash
# inline review comment — replies in its own thread
gh api "repos/$REPO/pulls/$PR/comments/$COMMENT_ID/replies" -F body=@/tmp/reply.md

# top-level comment or review summary — quote what you are answering
gh pr comment "$PR" --body-file /tmp/reply.md
```

## 7. Report

Summarise for the user: how many comments answered, how many accepted vs rejected, and
which files changed. Name anything you deliberately left alone.
