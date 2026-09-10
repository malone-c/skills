---
name: trebuchet
description: "Moves the current Claude Code session to a remote VM over SSH — syncs the working tree, copies the transcript, and resumes the conversation in a Herdr pane on the far side. Trigger words: `trebuchet`, `move this session to <host>`, `continue this on the VM`, `pick this up on <host>`"
argument-hint: "<ssh host> [remote repo path]"
---

# Trebuchet

Launch the session over the wall: same conversation, same working tree, running on a VM.

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

## 1. Preflight

```bash
HOST=<ssh host>
SID="$CLAUDE_CODE_SESSION_ID"
TRANSCRIPT=$(find ~/.claude/projects -name "$SID.jsonl")
LOCAL_REPO=$(git rev-parse --show-toplevel)
ssh -o BatchMode=yes "$HOST" true
```

`ssh <host> <cmd>` runs non-interactively, so a login-shell `PATH` does not apply and
`~/.local/bin` is usually missing. Resolve both binaries once and use absolute paths everywhere
after:

```bash
ssh "$HOST" 'command -v claude; command -v herdr || ls ~/.local/bin/herdr'
```

Call the herdr path `$RH`, then check the far side has a server to talk to:

```bash
ssh "$HOST" "$RH status | head -20; $RH session list"
```

No server means Herdr is not set up there yet. Stop and ask the user to run
`herdr machine add <ssh-target> --label <label>` locally — it installs and starts the remote server,
and needs an interactive terminal for its approval prompts. Do not attempt the install yourself.

## 2. Agree on the remote path

```bash
REMOTE_HOME=$(ssh "$HOST" 'echo $HOME')
REMOTE_REPO=${LOCAL_REPO/#$HOME/$REMOTE_HOME}
```

If the repo is not under `$HOME`, or the user passed a path as an argument, use that instead.
Confirm `REMOTE_REPO` with the user before writing anything to the VM. Everything downstream —
the slug, the workspace cwd, the path rewrite — is keyed on it, and getting it wrong scatters files
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
  | ssh "$HOST" "cat > ~/.claude/projects/$REMOTE_SLUG/$SID.jsonl"
```

The rewrite is what makes the history's file references resolve on the far side. It is a blunt
substitution over the whole transcript, so it also catches home paths that have nothing to do with
the repo — acceptable, and better than a history that points at directories the VM does not have.
Skip the rewrite entirely when both paths already match.

Carry the sidecar directory too when the session has one; it holds tool results the transcript
refers to by reference:

```bash
[ -d "$(dirname "$TRANSCRIPT")/$SID" ] && rsync -a "$(dirname "$TRANSCRIPT")/$SID/" "$HOST:.claude/projects/$REMOTE_SLUG/$SID/"
```

## 5. Start it in Herdr

Check whether the remote directory is trusted, because an untrusted one changes what happens next:

```bash
ssh "$HOST" "python3 -c \"import json,os;d=json.load(open(os.path.expanduser('~/.claude.json')));print(d.get('projects',{}).get('$REMOTE_REPO',{}).get('hasTrustDialogAccepted'))\""
```

Create a workspace at the repo and start the agent in its root pane:

```bash
ssh "$HOST" "$RH workspace create --cwd $REMOTE_REPO --label <repo-name> --no-focus"
ssh "$HOST" "$RH agent start <name> --kind claude --pane <root-pane-id> --timeout 60000 -- --resume $SID"
```

Read `root_pane.pane_id` out of the workspace response rather than guessing it, and use `--no-focus`
so the throw does not yank the remote TUI away from whatever the user has open there.

If the directory was not trusted, `agent start` returns `agent_not_ready` and the agent sits on the
folder-trust prompt. That is a success, not a failure — Claude is up and waiting. Report it and let
the user answer the prompt when they attach. Trusting a directory on the user's machine is their
decision, not something to send keys for.

Confirm the throw landed:

```bash
ssh "$HOST" "$RH agent read <name> --source visible --lines 40"
```

The last few exchanges of this conversation should be on screen.

## 6. Land

Tell the user, in this order:

1. **How to attach.** The saved machine in their local Herdr TUI, or
   `ssh -t $HOST '<herdr path> session attach default'`.
2. **The trust prompt**, if the agent is blocked on one.
3. **To stop working here.** Both machines now hold the same session id, and typing into either
   writes its own transcript from that point on. They never merge. Whichever side they choose, the
   other has to be left alone.

## Gotchas

- The transcript's last entry is normally a tool call that was still in flight, so the resumed
  session opens showing it as interrupted. Expected — the history above it is intact.
- `git diff HEAD` flattens the index. What was staged arrives unstaged.
- Ignored files do not travel: `.venv`, `node_modules`, build output, `.env`. Anything the session
  depended on that git does not track has to be rebuilt or copied on purpose.
- A remote `~/.claude/settings.json` carrying hook paths from another machine throws a
  `SessionStart:resume hook error` on arrival. Noisy but harmless, and it is the remote settings
  that are wrong, not the transcript — do not patch the copied session to work around it.
