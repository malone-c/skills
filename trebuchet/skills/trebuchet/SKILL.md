---
name: trebuchet
description: "Moves the current Claude Code session to a remote VM over SSH — syncs the working tree, copies the transcript, and resumes the conversation as a background Remote Control session on the far side, reachable from claude.ai or the terminal. Trigger words: `trebuchet`, `move this session to <host>`, `continue this on the VM`, `pick this up on <host>`"
argument-hint: "<ssh host> [remote repo path]"
---

# Trebuchet

Launch the session over the wall: same conversation, same working tree, running on a VM.

The far side runs it with native Claude Code — `claude --bg --remote-control --resume <id>
"TREBUCHET COMPLETE: …"`. That is a background session managed by the machine's Claude Code
supervisor: no terminal has to stay open, it survives your SSH disconnect, and Remote Control makes
it reachable from claude.ai/code, the Claude app, or a terminal on the VM. The trailing prompt is
what makes it start working on arrival rather than sit idle. No Herdr, no extra multiplexer.

Nothing here is destroyed. The local transcript stays on disk and the local repo is untouched —
trebuchet copies, it never moves — so a failed throw costs nothing but a stray workspace on the far
side.

Two things have to travel:

| | |
| --- | --- |
| The conversation | `~/.claude/projects/<slug>/<session-id>.jsonl`, and the `<session-id>/` directory beside it when one exists |
| The code | The commit, plus everything uncommitted |

`<slug>` is the absolute path of the session's working directory with every character that is not a
letter or a digit replaced by `-`. `/Users/cm/dev/skills` becomes `-Users-cm-dev-skills`. Home
differs between machines, so the local and remote slugs are never the same — compute both.

## Not disturbing an existing daemon

The user may already run Claude Code servers on the far side — a `claude remote-control` server as a
systemd unit, other background sessions, or both. A trebuchet throw is just one more background
session under the same per-user supervisor that already hosts them, so it coexists by design. Hold to
these and it stays out of their way:

- **Never touch their server.** Don't stop, restart, or reconfigure a `claude remote-control`
  process or its systemd unit. You are adding a session, not managing theirs.
- **Leave `CLAUDE_CONFIG_DIR` alone.** Setting it spawns a *separate* supervisor with its own
  session list, so the throw would vanish from their `claude agents` and their claude.ai list. Use
  the default (`~/.claude`) so the thrown session lands in the same supervisor as everything else.
- **Give the session a distinct `--name`.** Never reuse the name their server registers under (often
  the hostname, e.g. `dev-chris`). Name the throw after the repo and branch so the two are
  told apart in the claude.ai session list.
- **Throw into the repo directory.** A `claude remote-control` server keeps a per-directory resume
  record. The repo path differs from the server's working directory, so there is no collision — one
  more reason `REMOTE_REPO` must be the repo, not `$HOME`.

## Speed

A throw is four remote operations — preflight, sync, copy, launch — and should take about a
minute. Every `ssh` is a round trip, so batch each step into one command as the snippets below do,
and don't read anything the throw does not need (memory files, the transcript, the far side's other
sessions). The time sinks that have made this take five minutes are all avoidable and each is called
out where it bites: launching without a prompt, parsing the URL out of `claude logs`, and asking
about the remote path when the default is fine.

## 1. Preflight

Local and remote, one command each:

```bash
HOST=<ssh host>
SID="$CLAUDE_CODE_SESSION_ID"
TRANSCRIPT=$(find ~/.claude/projects -name "$SID.jsonl")
LOCAL_REPO=$(git rev-parse --show-toplevel)
BRANCH=$(git branch --show-current); SHA=$(git rev-parse HEAD)
git fetch -q origin; git branch -r --contains "$SHA" | head -1; git status --short
```

```bash
ssh -o BatchMode=yes "$HOST" 'echo HOME=$HOME; RC=$(command -v claude || ls ~/.local/bin/claude); echo RC=$RC; $RC --version; $RC agents --json >/dev/null && echo agents-ok'
```

`ssh <host> <cmd>` runs non-interactively, so a login-shell `PATH` does not apply and
`~/.local/bin` is usually missing — that is why the binary is resolved once and used by absolute path
everywhere after, as `$RC`.

The launch needs Claude Code **v2.1.257 or later** on the far side, the floor for resuming a
conversation into a background session (`--bg --resume`). Older than that, stop and ask the user to
update Claude Code on the VM.

Remote Control signs in with the machine's saved claude.ai account, so the VM must already be logged
in with a subscription account (API-key auth can't drive Remote Control). `agents --json` succeeding
is enough proof.

## 2. Agree on the remote path

```bash
REMOTE_HOME=<from preflight>
REMOTE_REPO=${LOCAL_REPO/#$HOME/$REMOTE_HOME}
ssh "$HOST" "cd $REMOTE_REPO 2>/dev/null && git branch --show-current && git rev-parse --short HEAD && git status --short | head" || echo absent
```

If the repo is not under `$HOME`, or the user passed a path as an argument, use that instead.
Everything downstream — the slug, the session's cwd, the path rewrite — is keyed on it, and getting
it wrong scatters files in a directory nobody asked for.

Confirm the path with the user **only when the default is doubtful**: it does not exist, it is not a
git checkout, or it has uncommitted changes. A mirror of the local path that is already checked out
and clean is what the user expects; asking about it is a round trip to a human for nothing.

## 3. Sync the working tree

Preflight already told you what needs to move: whether `$SHA` is on origin, and what
`git status --short` holds.

**The checkout.** Clone it if it is not there:

```bash
ssh "$HOST" "test -d $REMOTE_REPO/.git" || ssh "$HOST" "git clone $(git remote get-url origin) $REMOTE_REPO"
```

If it is there, step 2 showed its `git status --short`. Uncommitted work in the remote checkout is
someone's unsaved state — show it to the user and stop rather than resetting over it.

**The commit.** When `$SHA` is already on origin:

```bash
ssh "$HOST" "cd $REMOTE_REPO && git fetch -q origin && git checkout -q -B $BRANCH $SHA && git rev-parse --short HEAD"
```

`fetch origin`, not `fetch --all`: a checkout that has sat for months has hundreds of commits to
pull, and every extra remote multiplies that.

When it is not, ship the commits directly rather than pushing to origin on the user's behalf:

```bash
git bundle create /tmp/treb.bundle "$BRANCH"
scp /tmp/treb.bundle "$HOST:/tmp/"
ssh "$HOST" "cd $REMOTE_REPO && git fetch /tmp/treb.bundle $BRANCH:refs/trebuchet/$BRANCH && git checkout -B $BRANCH refs/trebuchet/$BRANCH"
```

Pushing to origin is a fine alternative when the branch is meant to be shared, but ask first —
it is outward-facing and the bundle is not.

**The uncommitted work.** Tracked changes as a patch, untracked files over rsync:

```bash
git diff HEAD > /tmp/treb.patch
scp /tmp/treb.patch "$HOST:/tmp/"
ssh "$HOST" "cd $REMOTE_REPO && git apply /tmp/treb.patch"

git ls-files --others --exclude-standard > /tmp/treb-untracked.txt
[ -s /tmp/treb-untracked.txt ] && rsync -a --files-from=/tmp/treb-untracked.txt "$LOCAL_REPO/" "$HOST:$REMOTE_REPO/"
```

Skip both when `git status --short` is empty. An untracked directory that predates the session and
has nothing to do with the task — a 60 MB scratch checkout, say — is the user's, not the session's:
leave it and name it in the landing report rather than shipping it.

Then diff the two `git status --short` outputs and report any line that did not survive.

## 4. Copy the session

```bash
LOCAL_SLUG=$(printf '%s' "$LOCAL_REPO" | sed 's/[^a-zA-Z0-9]/-/g')
REMOTE_SLUG=$(printf '%s' "$REMOTE_REPO" | sed 's/[^a-zA-Z0-9]/-/g')

sed "s|$LOCAL_REPO|$REMOTE_REPO|g; s|$LOCAL_SLUG|$REMOTE_SLUG|g; s|$HOME|$REMOTE_HOME|g" "$TRANSCRIPT" \
  | grep -v '"type":"bridge-session"' \
  | ssh "$HOST" "mkdir -p ~/.claude/projects/$REMOTE_SLUG && cat > ~/.claude/projects/$REMOTE_SLUG/$SID.jsonl"
```

Two transforms here, both deliberate:

- **The path rewrite** is what makes the history's file references resolve on the far side. It is a
  blunt substitution over the whole transcript, so it also catches home paths that have nothing to
  do with the repo — acceptable, and better than a history that points at directories the VM does
  not have. The slug clause covers the paths the transcript holds *under* `~/.claude/projects/`:
  persisted tool results and the memory directory are keyed by slug, and `s|$HOME|…|` alone leaves
  `-Users-cm-…` inside a `/home/cm/.claude/projects/` path, which resolves to nothing. Skip the
  whole rewrite when both paths already match.
- **Dropping `bridge-session` lines** strips this conversation's Remote Control reconnection record.
  Those records name the claude.ai session the *local* terminal owns; carried across, the resumed
  session would try to reconnect to it and contend with the machine you threw from. Without them, the
  far side registers a fresh Remote Control session cleanly. If the local session never had Remote
  Control on, there are no such lines and the `grep` is a no-op.

Carry the sidecar directory too when the session has one; it holds tool results the transcript
refers to by reference:

```bash
[ -d "$(dirname "$TRANSCRIPT")/$SID" ] && rsync -a "$(dirname "$TRANSCRIPT")/$SID/" "$HOST:.claude/projects/$REMOTE_SLUG/$SID/"
```

## 5. Launch it

Start the session in the background, in the repo directory, with Remote Control on, a distinct
name, **and a prompt** — the prod that tells the far side it has landed and to carry on:

```bash
NAME="<repo-name>/$BRANCH"
PROD="TREBUCHET COMPLETE: you are now on $HOST, in $REMOTE_REPO at $(git rev-parse --short HEAD) on $BRANCH, forked from session $SID. Pick up the task exactly where the transcript leaves off; the last tool call shows as interrupted because the throw cut it, so redo it. <one line naming the task and its next step>"
LAUNCH=$(ssh "$HOST" "cd $REMOTE_REPO && $RC --bg --remote-control --fork-session --name '$NAME' --resume $SID \"$PROD\"" < /dev/null)
printf '%s\n' "$LAUNCH"
NEW_ID=$(printf '%s' "$LAUNCH" | grep -o -E 'backgrounded · [0-9a-f]{8}' | awk '{print $NF}')
```

**The prompt is not optional.** Without one the session parks at `idle — send a prompt to start`
and does nothing until somebody types into it — the throw looks complete and isn't. There is no
`claude send`; the only ways to prod an idle background session are to attach to it interactively
or to stop it and relaunch with a prompt, and relaunching a stopped session *with any flags* forks a
copy under a new id (the note reads "keeps its own saved options, so the flags you passed started a
copy"), leaving a dead duplicate to unpin. Passing the prompt at launch avoids all of that. Start it
with the literal `TREBUCHET COMPLETE:` so the far side — and anyone reading the transcript later —
can see where the throw happened, and end with the task's next step in your own words: the
transcript carries the history, but a one-line restatement is what turns an idle resume into work.

What each piece buys:

- **`--bg`** hands the session to the supervisor daemon and returns immediately. No terminal stays
  attached, and it survives your SSH disconnect. It also means the workspace-trust dialog is skipped
  (background sessions are non-interactive), so a directory Claude has never seen on the VM just runs
  — none of Herdr's folder-trust waiting.
- **`--remote-control`** registers the session with claude.ai so you can reach it from a browser or
  the Claude app.
- **`--fork-session`** is what keeps the two machines apart. It reads the copied transcript, carries
  the full history, and starts the far side under a *new* session id, so the VM and your laptop no
  longer share one. Without it, `--resume $SID` would continue in place under the same id, and typing
  on either side would fork the transcript from that point — the two writing over the same identity.
  The fork is the clean version of what happens anyway: a copy that shares history up to the throw
  and diverges after it.
- **`--resume $SID`** names the conversation to fork from — the transcript you copied in step 4.
- **The trailing prompt** is the first message of the forked session, so it starts working
  immediately instead of waiting at the prompt.
- **`< /dev/null`** keeps ssh from holding a stdin the background launcher does not need.

The command prints the *new* short id — assigned by the fork, so read it from the output
(`$NEW_ID` above) rather than deriving it from `$SID`:

```
backgrounded · 4a2dec70 · <name>
```

Then **pin it**, or the supervisor will retire it. The `--bg` daemon treats background sessions as
agents that finish a job: one that sits at an idle prompt — waiting on you, which a thrown session
does most of the time — is retired after ~8h (`bg retire <id>: idle-prompt, idle 8h` in
`~/.claude/daemon.log`), and the daemon then exits with no workers left. Pinned sessions are exempt
and get respawned if they go stale. The pin list is `~/.claude/jobs/pins.json`, a JSON array of
short ids, re-read on every sweep:

```bash
ssh "$HOST" "jq --arg id $NEW_ID '. + [\$id] | unique' ~/.claude/jobs/pins.json > ~/.claude/jobs/pins.json.tmp && mv ~/.claude/jobs/pins.json.tmp ~/.claude/jobs/pins.json"
```

The same toggle is `ctrl+t` on the session's row in `claude agents`, where it shows under **Pinned**.

Pin, then read the URL and the state in the same round trip, from the job record rather than the
log. `~/.claude/jobs/<id>/state.json` holds `bridgeSessionId` (`cse_…`), which is the claude.ai
session id with a different prefix, plus `state` and a one-line `detail` of what the session is
doing:

```bash
ssh "$HOST" "jq --arg id $NEW_ID '. + [\$id] | unique' ~/.claude/jobs/pins.json > ~/.claude/jobs/pins.json.tmp && mv ~/.claude/jobs/pins.json.tmp ~/.claude/jobs/pins.json; sleep 15; jq -r '\"https://claude.ai/code/\" + (.bridgeSessionId | sub(\"^cse_\"; \"session_\")), .state, .detail' ~/.claude/jobs/$NEW_ID/state.json"
```

`bridgeSessionId` is written once Remote Control connects, a few seconds after launch — hence the
sleep. `state` should read `working` (or `blocked` on a permission prompt, which `claude attach`
answers); `idle` means the prompt did not reach it. `detail` is the session's own summary of what
it is doing and is the fastest proof that it picked up the right task.

Do not read the URL or the state out of `claude logs`. That is raw terminal output: one huge line
of cursor-positioning escapes (`ESC[74G`) that land in the middle of the URL, so a `grep` for it
matches nothing and `tail -40` shows garbage. If you must read the log, strip the escapes first —
`perl -pe 's/\e\[[\d;?]*[A-Za-z]//g'` (macOS `sed` does not understand `\x1b`).

## 6. Land

Tell the user, in this order:

1. **How to attach.** Any of:
   - Open the claude.ai/code URL in a browser, or find the session by its `<name>` in the session
     list at claude.ai/code or in the Claude app.
   - On the VM: `ssh -t $HOST '<claude path> attach $NEW_ID'` opens it in a terminal.
2. **That it is working**, quoting `state` and `detail` from the job record, so the user does not
   have to open it to find out whether it started.
3. **That it is a fork, not a handoff.** The VM session has its own id and shares this conversation's
   history only up to the throw. From here the two diverge: work on the VM does not appear on the
   laptop and the reverse, and they never merge. Both are usable — pick the one you mean to continue
   on and let the other be, or the far side is yours to abandon if the throw was just to borrow the
   VM's hardware.
4. **What did not travel**, if anything: an untracked directory you left behind, a hook error on
   arrival.

The background session keeps running on the VM whether or not anyone is attached. To end it later:
`ssh "$HOST" "<claude path> stop $NEW_ID"`, unpin it (`ctrl+t` in `claude agents`, or drop the id
from `~/.claude/jobs/pins.json`), and `claude rm` to drop it from the list.

## Gotchas

- A throw that vanished after some hours with `claude logs` reporting `connect ENOENT
  /tmp/cc-daemon-<uid>/.../control.sock` was idle-retired, not killed — it was never pinned. The job
  record survives under `~/.claude/jobs/<id>/`: pin it and `claude respawn <id>` brings it back.
- The transcript's last entry is normally a tool call that was still in flight, so the resumed
  session opens showing it as interrupted. Expected — the history above it is intact, and the
  launch prompt tells the far side to redo that call.
- A session that landed idle (launched without a prompt) cannot be prodded from outside. To
  recover it: `claude stop <id>`, then `claude --bg --resume <full session id> "<prompt>"` with
  **no other flags** — the stopped session keeps its saved options, and passing any flag starts a
  copy under a new id instead. If a copy was started anyway, unpin the original: pins are by short
  id and the daemon respawns anything pinned.
- Every throw forks, so throwing the same session twice just lands two independent VM sessions, each
  with its own id and history up to its throw. Neither disturbs the other or the laptop.
- `git diff HEAD` flattens the index. What was staged arrives unstaged.
- Ignored files do not travel: `.venv`, `node_modules`, build output, `.env`. Anything the session
  depended on that git does not track has to be rebuilt or copied on purpose.
- A remote `~/.claude/settings.json` carrying hook paths from another machine throws a
  `SessionStart:resume hook error` on arrival. Noisy but harmless, and it is the remote settings
  that are wrong, not the transcript — do not patch the copied session to work around it.
