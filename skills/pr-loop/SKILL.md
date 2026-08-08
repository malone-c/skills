---
name: pr-loop
description: Keep answering review comments on a PR on a timer until the reviewers go quiet. Creates the PR first if the branch has none. Use when asked to watch a PR, keep up with review comments, or poll for feedback.
argument-hint: "<PR number> <interval, e.g. 5m — default 10m>"
---

# PR loop

Arm a recurring pass of `respond-to-comments` over one PR, and disarm it once two
consecutive passes find nothing new.

Two entry points. `/pr-loop tick <PR>` is the internal one the timer fires — if the
first argument is `tick`, skip to [Tick](#tick).

## Arm

### 1. Resolve the PR

In order, stop at the first that works:

1. A PR number given as an argument.
2. `gh pr view --json number -q .number` — the PR for the current branch.
3. A PR created earlier in this conversation.
4. None of the above: create one with the `pr-description` skill, then use its number.

### 2. Resolve the interval

Default `10m`. Map it to a 5-field cron expression:

| Argument | Cron |
|---|---|
| `5m` | `*/5 * * * *` |
| `10m` | `*/10 * * * *` |
| `15m` | `*/15 * * * *` |
| `30m` | `*/30 * * * *` |
| `1h` | `7 * * * *` |

For an interval that does not divide 60, `*/N` still works but the last slot before the
hour is short. For intervals over an hour use `<off-minute> */H * * *`.

### 3. Check nothing is already armed

Call `CronList`. If a job's prompt already contains `/pr-loop tick <PR>`, say so and stop
— do not arm a second one.

### 4. Prime the state

```bash
echo '{"pr": <PR>, "quiet_rounds": 0}' > "${TMPDIR:-/tmp}/pr-loop-<PR>.json"
```

### 5. Run one pass now

Invoke `respond-to-comments` for the PR immediately, then apply the [Tick](#tick)
bookkeeping to its result. Waiting a full interval before the first pass wastes the
arming turn.

### 6. Arm the loop

Invoke the `loop` skill:

```
/loop <interval> /pr-loop tick <PR>
```

Then tell the user the PR, the interval, and that the loop is session-scoped.

## Tick

Fired by the timer. Do exactly this:

1. Read `${TMPDIR:-/tmp}/pr-loop-<PR>.json`. If it is missing, treat `quiet_rounds` as 0.
2. Invoke `respond-to-comments` for the PR.
3. If it answered one or more comments, set `quiet_rounds` to 0. If it found nothing
   unanswered, add 1.
4. Write the file back.
5. If `quiet_rounds` is 2 or more, [disarm](#disarm).

A pass that answered comments resets the counter, so the loop only ends after two
genuinely quiet intervals in a row — not two intervals in which you happened to do
nothing.

Do not call `ScheduleWakeup` from a tick. The cron fires the next tick on its own;
`ScheduleWakeup` is for self-paced loops and would double up.

## Disarm

```
CronList  →  find the job whose prompt contains "/pr-loop tick <PR>"
CronDelete(id)
```

Delete the state file, then tell the user the loop stopped, how many passes ran, and
what was answered across them.

Disarm the same way whenever the user asks you to stop watching the PR, and when the PR
is merged or closed — check `gh pr view <PR> --json state -q .state` on each tick and
stop on anything other than `OPEN`.

## What to tell the user when arming

These follow from the timer being a session cron, and they will notice all three:

- It dies when this Claude Code session ends. It is not a background service.
- It only fires while the session is idle, so a long turn delays a tick.
- Recurring jobs auto-expire after 7 days.
