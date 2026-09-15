# trebuchet

A Claude Code skill for stopping work on one machine and picking the same conversation up on
another. You are mid-session on a laptop, the job wants a GPU or a fast disk or a network you do not
have, and starting over on the VM means re-explaining everything you just explained.

## `/trebuchet`

```
/trebuchet <ssh host> [remote repo path]
```

Carries two things to the VM and starts Claude there:

- **The conversation.** The session transcript out of `~/.claude/projects/`, with local paths
  rewritten to their remote equivalents so the history's file references still resolve.
- **The code.** The commit — over `git fetch` when it is already on origin, over `git bundle` when
  it is not — plus tracked changes as a patch and untracked files over rsync.

Then it resumes the session on the far side with native Claude Code:

```
claude --bg --remote-control --resume <session-id>
```

That is a background session under the VM's Claude Code supervisor — no terminal has to stay open, it
survives your SSH disconnect, and Remote Control makes it reachable from claude.ai/code, the Claude
app, or a terminal on the VM. No Herdr or other multiplexer required.

Nothing local is destroyed. The transcript is copied, the repo is untouched, and a throw that fails
halfway costs an unused workspace on the VM.

## Coexisting with a running daemon

If the VM already runs Claude Code servers — a `claude remote-control` systemd unit, other
background sessions, or both — the throw is just one more background session under the same per-user
supervisor, so it coexists by design. The skill keeps out of their way: it never touches their
server, leaves `CLAUDE_CONFIG_DIR` at its default so the session lands in the same supervisor,
names the throw after the repo and branch (never the server's name) so the two are distinct in the
claude.ai session list, and runs it in the repo directory rather than the server's working directory.

## What it will not do

- **Log in on the VM.** Remote Control needs the machine signed in with a claude.ai subscription
  account. A VM already running Remote Control or background sessions is logged in; the skill checks
  and stops if it can't reach the supervisor.
- **Reset over uncommitted work in the remote checkout.** It shows you what is there and stops.
- **Push to origin without asking.** Unpushed commits go across as a bundle by default.

The workspace-trust prompt is a non-issue now: background sessions are non-interactive, so the far
side runs a directory it has never seen without waiting on a trust dialog.

## Known limits

Staged and unstaged changes arrive merged, because the patch is a single `git diff HEAD`. Ignored
files do not travel at all — `.venv`, `node_modules`, build output, `.env` are yours to recreate.
And both machines end up holding the same session id, so once you have thrown, only one side can be
typed into; they do not merge back.

## License

MIT
