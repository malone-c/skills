---
name: trebuchet
description: "Moves the current Claude Code session to a remote VM over SSH — syncs the working tree, copies the transcript, and resumes the conversation as a background Remote Control session on the far side, reachable from claude.ai or the terminal. Trigger words: `trebuchet`, `move this session to <host>`, `continue this on the VM`, `pick this up on <host>`"
argument-hint: "<ssh host> [remote repo path]"
---

# Trebuchet

Launch the session over the wall: same conversation, same working tree, running on a VM.

The far side runs it with native Claude Code — `claude --bg --remote-control --resume <id>`. That is
a background session managed by the machine's Claude Code supervisor: no terminal has to stay open,
it survives your SSH disconnect, and Remote Control makes it reachable from claude.ai/code, the
Claude app, or a terminal on the VM. No Herdr, no extra multiplexer.

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

## 1. Preflight

```bash
HOST=<ssh host>
SID="$CLAUDE_CODE_SESSION_ID"
TRANSCRIPT=$(find ~/.claude/projects -name "$SID.jsonl")
LOCAL_REPO=$(git rev-parse --show-toplevel)
ssh -o BatchMode=yes "$HOST" true
```

`ssh <host> <cmd>` runs non-interactively, so a login-shell `PATH` does not apply and
`~/.local/bin` is usually missing. Resolve the binary once and use its absolute path everywhere
after — call it `$RC`:

```bash
ssh "$HOST" 'command -v claude || ls ~/.local/bin/claude'
ssh "$HOST" "$RC --version"
```

The launch needs Claude Code **v2.1.257 or later** on the far side, the floor for resuming a
conversation into a background session (`--bg --resume`). Older than that, stop and ask the user to
update Claude Code on the VM.

Remote Control signs in with the machine's saved claude.ai account, so the VM must already be logged
in with a subscription account (API-key auth can't drive Remote Control). A machine that already runs
a `claude remote-control` server or background sessions is logged in; if in doubt, `ssh "$HOST" "$RC
agents --json"` succeeding is enough to proceed.

## 2. Agree on the remote path

```bash
REMOTE_HOME=$(ssh "$HOST" 'echo $HOME')
REMOTE_REPO=${LOCAL_REPO/#$HOME/$REMOTE_HOME}
```

If the repo is not under `$HOME`, or the user passed a path as an argument, use that instead.
Confirm `REMOTE_REPO` with the user before writing anything to the VM. Everything downstream —
the slug, the session's cwd, the path rewrite — is keyed on it, and getting it wrong scatters files
in a directory nobody asked for.

## 3. Sync the working tree

Work out what actually needs to move before moving anything:

```bash
BRANCH=$(git branch --show-current)
SHA=$(git rev-parse HEAD)
git status --short
```

**The checkout.** Clone it if it is not there:

```bash
ssh "$HOST" "test -d $REMOTE_REPO/.git" || ssh "$HOST" "git clone $(git remote get-url origin) $REMOTE_REPO"
```

If it is there, check `git status --short` on the far side first. Uncommitted work in the remote
checkout is someone's unsaved state — show it to the user and stop rather than resetting over it.

**The commit.** When `$SHA` is already on the remote's origin:

```bash
ssh "$HOST" "cd $REMOTE_REPO && git fetch --all && git checkout -B $BRANCH $SHA"
```

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

Then diff the two `git status --short` outputs and report any line that did not survive.

## 4. Copy the session

```bash
REMOTE_SLUG=$(printf '%s' "$REMOTE_REPO" | sed 's/[^a-zA-Z0-9]/-/g')
ssh "$HOST" "mkdir -p ~/.claude/projects/$REMOTE_SLUG"

sed "s|$LOCAL_REPO|$REMOTE_REPO|g; s|$HOME|$REMOTE_HOME|g" "$TRANSCRIPT" \
  | grep -v '"type":"bridge-session"' \
  | ssh "$HOST" "cat > ~/.claude/projects/$REMOTE_SLUG/$SID.jsonl"
```

Two transforms here, both deliberate:

- **The path rewrite** is what makes the history's file references resolve on the far side. It is a
  blunt substitution over the whole transcript, so it also catches home paths that have nothing to
  do with the repo — acceptable, and better than a history that points at directories the VM does
  not have. Skip it entirely when both paths already match.
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

Start the session in the background, in the repo directory, with Remote Control on and a distinct
name:

```bash
NAME="<repo-name>/$BRANCH"
LAUNCH=$(ssh "$HOST" "cd $REMOTE_REPO && $RC --bg --remote-control --fork-session --name '$NAME' --resume $SID" < /dev/null)
printf '%s\n' "$LAUNCH"
NEW_ID=$(printf '%s' "$LAUNCH" | grep -o -E 'backgrounded · [0-9a-f]{8}' | awk '{print $NF}')
```

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
- **`< /dev/null`** keeps ssh from holding a stdin the background launcher does not need.

The command prints the *new* short id and the session's claude.ai URL — the id is assigned by the
fork, so read it from the output (`$NEW_ID` above) rather than deriving it from `$SID`:

```
backgrounded · 4a2dec70 · <name>
```

Pull the URL from the session's log:

```bash
ssh "$HOST" "$RC logs $NEW_ID" | grep -o -E 'https://claude.ai/code/[A-Za-z0-9_]+' | tail -1
```

Confirm the throw landed by reading the log — the last few exchanges of this conversation, and an
`/rc is active` line with the URL, should be there:

```bash
ssh "$HOST" "$RC logs $NEW_ID" | tail -40
```

## 6. Land

Tell the user, in this order:

1. **How to attach.** Any of:
   - Open the claude.ai/code URL in a browser, or find the session by its `<name>` in the session
     list at claude.ai/code or in the Claude app.
   - On the VM: `ssh -t $HOST '<claude path> attach $NEW_ID'` opens it in a terminal.
2. **That it is a fork, not a handoff.** The VM session has its own id and shares this conversation's
   history only up to the throw. From here the two diverge: work on the VM does not appear on the
   laptop and the reverse, and they never merge. Both are usable — pick the one you mean to continue
   on and let the other be, or the far side is yours to abandon if the throw was just to borrow the
   VM's hardware.

The background session keeps running on the VM whether or not anyone is attached. To end it later:
`ssh "$HOST" "<claude path> stop $NEW_ID"`, and `claude rm` to drop it from the list.

## Gotchas

- The transcript's last entry is normally a tool call that was still in flight, so the resumed
  session opens showing it as interrupted. Expected — the history above it is intact.
- Every throw forks, so throwing the same session twice just lands two independent VM sessions, each
  with its own id and history up to its throw. Neither disturbs the other or the laptop.
- `git diff HEAD` flattens the index. What was staged arrives unstaged.
- Ignored files do not travel: `.venv`, `node_modules`, build output, `.env`. Anything the session
  depended on that git does not track has to be rebuilt or copied on purpose.
- A remote `~/.claude/settings.json` carrying hook paths from another machine throws a
  `SessionStart:resume hook error` on arrival. Noisy but harmless, and it is the remote settings
  that are wrong, not the transcript — do not patch the copied session to work around it.
